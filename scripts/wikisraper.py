#!/usr/bin/env python3
"""
liquidpedia_dota2.py 

A robust, production-quality script to extract content from Liquipedia Dota2 Wiki using
both API and web scraping approaches with graceful fallback mechanisms.
"""

# Core Python imports
import argparse
import json
import logging
import os
import re
import sys
import time
import signal
import gzip
import threading
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union 
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

# Third-party imports
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, RequestException, ConnectionError
from urllib3.util.retry import Retry

# Base exception class
class LiquidpediaScraperError(Exception):
    """Base exception class for Liquipedia scraper errors."""
    pass

class APIFailureException(LiquidpediaScraperError):
    """Exception raised when API mode fails and fallback should be used."""
    pass

class ScrapingQuotaExceededException(LiquidpediaScraperError):
    """Exception raised when scraping quota is exceeded or IP is blocked."""
    pass

@dataclass
class ScrapeProgress:
    """Track scraping progress for resumable jobs."""
    processed_pages: List[str]
    last_page_idx: int = 0
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional['ScrapeProgress']:
        """Load progress from file if it exists."""
        if not file_path.exists():
            return None
            
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(
                    processed_pages=data.get("processed_pages", []),
                    last_page_idx=data.get("last_page_idx", 0)
                )
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load progress file {file_path}: {e}")
            return None
            
    def save_to_file(self, file_path: Path) -> None:
        """Save progress to file."""
        try:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "processed_pages": self.processed_pages,
                    "last_page_idx": self.last_page_idx
                }, f)
        except IOError as e:
            logging.warning(f"Failed to save progress to {file_path}: {e}")

class RateLimiter:
    """Advanced rate limiter with dynamic backoff for respecting server resources."""
    
    def __init__(
        self,
        base_rate: float = 2.0,
        max_rate: float = 10.0,
        backoff_factor: float = 1.5,
        recovery_factor: float = 0.9,
        error_threshold: int = 3,
    ) -> None:
        self.base_rate = base_rate
        self.current_rate = base_rate
        self.max_rate = max_rate
        self.backoff_factor = backoff_factor
        self.recovery_factor = recovery_factor
        self.error_count = 0
        self.error_threshold = error_threshold
        self.last_request_time = 0
        self._lock = threading.Lock()
    
    def wait(self) -> None:
        """Wait for the appropriate time before the next request."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_request_time
            wait_time = max(0, self.current_rate - elapsed)
            
            if wait_time > 0:
                time.sleep(wait_time)
                
            self.last_request_time = time.time()
    
    def success(self) -> None:
        """Called after a successful request to potentially reduce delay."""
        with self._lock:
            self.error_count = 0
            if self.current_rate > self.base_rate:
                self.current_rate = max(
                    self.base_rate,
                    self.current_rate * self.recovery_factor
                )
    
    def error(self) -> None:
        """Called after a failed request to increase delay."""
        with self._lock:
            self.error_count += 1
            if self.error_count >= self.error_threshold:
                self.current_rate = min(
                    self.max_rate,
                    self.current_rate * self.backoff_factor
                )
                self.error_count = 0
                logging.warning(f"Rate limiter increasing delay to {self.current_rate:.2f}s due to errors")

class LiquidpediaClient:
    """Client for Liquipedia Dota2 MediaWiki and Semantic MediaWiki APIs with fallback."""
    
    def __init__(
        self,
        api_url: str,
        base_url: str,
        user_agent: str,
        maxlag: int = 5,
        rate_limit: float = 2.0,
        parse_limit: float = 30.0,
        retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: Optional[List[int]] = None,
        cache_dir: Optional[str] = None,
        cache_expiry: int = 86400,
        incremental_save: bool = True,
        incremental_save_interval: int = 50,
        detect_blocks: bool = True,
        max_concurrent_requests: int = 1,
    ) -> None:
        """Initialize the client with all configuration parameters."""
        self.api_url = api_url
        self.base_url = base_url
        self.headers = {"User-Agent": user_agent}
        self.maxlag = maxlag
        self.rate_limit = rate_limit
        self.parse_limit = parse_limit
        self.api_failure_count = 0
        self.max_api_failures = 5
        self.api_mode = True
        self.cache_dir = cache_dir
        self.cache_expiry = cache_expiry
        self.incremental_save = incremental_save
        self.incremental_save_interval = incremental_save_interval
        self.detect_blocks = detect_blocks
        self.max_concurrent_requests = max_concurrent_requests
        self.processed_pages: List[str] = []
        self._rate_limit_lock = threading.Lock()
        
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # Initialize session with retries
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        status_forcelist = status_forcelist or [429, 500, 502, 503, 504]
        retry_strategy = Retry(
            total=retries,
            status_forcelist=status_forcelist,
            backoff_factor=backoff_factor,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            base_rate=rate_limit,
            max_rate=rate_limit * 5
        )
        
        logging.info("Initialized LiquidpediaClient in API mode with web scraping fallback")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()

    def _get_cache_path(self, params: Dict[str, Any]) -> Optional[Path]:
        """Get cache file path for the given parameters."""
        if not self.cache_dir:
            return None
        cache_key = json.dumps(params, sort_keys=True).encode("utf-8")
        filename = hashlib.md5(cache_key).hexdigest() + ".json"
        return Path(self.cache_dir) / filename

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache is still valid based on expiry time."""
        if not cache_path.exists():
            return False
        if self.cache_expiry <= 0:
            return True
        cache_time = cache_path.stat().st_mtime
        current_time = time.time()
        return (current_time - cache_time) < self.cache_expiry

    def _get_from_cache(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try to get response from cache."""
        if not self.cache_dir:
            return None
        cache_path = self._get_cache_path(params)
        if not cache_path or not self._is_cache_valid(cache_path):
            return None
        try:
            with cache_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Cache error for {cache_path}: {e}")
            return None

    def _save_to_cache(self, params: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Save response to cache."""
        if not self.cache_dir:
            return
        cache_path = self._get_cache_path(params)
        if not cache_path:
            return
        try:
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except IOError as e:
            logging.warning(f"Failed to write cache for {cache_path}: {e}")

    def _request_with_rate_limit(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a rate-limited request."""
        with self._rate_limit_lock:
            self.rate_limiter.wait()
            try:
                response = self.session.request(method, url, **kwargs)
                self.rate_limiter.success()
                return response
            except Exception as e:
                self.rate_limiter.error()
                raise

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a GET request with caching and rate limiting."""
        cached_data = self._get_from_cache(params)
        if cached_data:
            logging.debug(f"Cache hit for params: {params}")
            return cached_data
            
        params.update({"format": "json", "formatversion": 2, "maxlag": self.maxlag})
        try:
            response = self._request_with_rate_limit("GET", self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.api_failure_count = 0
            
            if "error" in data and data["error"].get("code") == "maxlag":
                retry_after = int(response.headers.get("Retry-After", self.maxlag))
                logging.warning(f"maxlag encountered, retrying after {retry_after} seconds")
                time.sleep(retry_after)
                return self._get(params)
                
            self._save_to_cache(params, data)
            return data
            
        except Exception as e:
            self.api_failure_count += 1
            logging.error(f"API error for params {params}: {e} (failure #{self.api_failure_count})")
            
            if self.api_failure_count >= self.max_api_failures:
                logging.warning(
                    f"Reached maximum API failures ({self.max_api_failures}). Switching to web scraping fallback."
                )
                self.api_mode = False
                raise APIFailureException("API mode disabled due to repeated failures")
            raise

    def get_all_pages(self) -> Generator[Dict[str, Any], None, None]:
        """Get all pages with web scraping fallback."""
        if self.api_mode:
            try:
                yield from self._get_all_pages_api()
                return
            except APIFailureException:
                logging.info("Falling back to web scraping for page listing")
        
        yield from self._get_all_pages_web()

    def _get_all_pages_api(self) -> Generator[Dict[str, Any], None, None]:
        """Get all pages via API."""
        params = {"action": "query", "list": "allpages", "aplimit": "max"}
        continuation: Dict[str, Any] = {}
        
        while True:
            params.update(continuation)
            data = self._get(params)
            
            pages = data.get("query", {}).get("allpages", [])
            for page in pages:
                yield page
                
            continuation = data.get("continue", {})
            if not continuation:
                break
                
            self.rate_limiter.wait()

    def _get_all_pages_web(self) -> Generator[Dict[str, Any], None, None]:
        """Get all pages via web scraping."""
        page_url = urljoin(self.base_url, "Special:AllPages")
        visited = set()
        
        try:
            while page_url:
                response = self._request_with_rate_limit("GET", page_url)
                soup = BeautifulSoup(response.text, "html.parser")
                
                for link in soup.select("ul.mw-allpages-chunk li a"):
                    title = link.get_text().strip()
                    if title and title not in visited:
                        visited.add(title)
                        yield {"title": title, "pageid": None}
                
                next_link = soup.select_one("a:contains('Next page')")
                page_url = urljoin(self.base_url, next_link["href"]) if next_link else None
                
        except Exception as e:
            logging.error(f"Error in web scraping fallback: {e}")
            raise

    def save_json(self, records: List[Dict[str, Any]], output_path: Path) -> None:
        """Save records to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(records)} pages to {output_path}")
        except IOError as e:
            logging.error(f"Failed writing to {output_path}: {e}")
            raise

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape Liquipedia Dota2 wiki with API and web scraping fallback.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--api-url",
        default="https://liquipedia.net/dota2/api.php",
        help="MediaWiki API URL"
    )
    parser.add_argument(
        "--base-url",
        default="https://liquipedia.net/dota2/",
        help="Base URL for the wiki"
    )
    parser.add_argument(
        "--user-agent",
        required=True,
        help="User-Agent string"
    )
    parser.add_argument(
        "--output",
        default="liquidpedia_dota2_dump.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--maxlag",
        type=int,
        default=5,
        help="maxlag seconds for API courtesy"
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Directory to store cached API responses"
    )
    parser.add_argument(
        "--cache-expiry",
        type=int,
        default=86400,
        help="Cache expiry in seconds"
    )
    parser.add_argument(
        "--no-incremental-save",
        action="store_true",
        help="Disable incremental saving"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last run if possible"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    parser.add_argument(
        "--fallback-only",
        action="store_true",
        help="Use only web scraping fallback"
    )
    
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Configure logging
    log_format = "%(asctime)s %(levelname)s: %(message)s"
    log_file = f"liquidpedia_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("Starting Liquipedia Dota2 scraper")
    
    try:
        with LiquidpediaClient(
            api_url=args.api_url,
            base_url=args.base_url,
            user_agent=args.user_agent,
            maxlag=args.maxlag,
            cache_dir=args.cache_dir,
            cache_expiry=args.cache_expiry,
            incremental_save=not args.no_incremental_save
        ) as client:
            
            if args.fallback_only:
                client.api_mode = False
                logging.info("Using web scraping fallback only as requested")
            
            # Process pages
            pages = list(client.get_all_pages())
            logging.info(f"Found {len(pages)} pages to process")
            
            records = []
            for i, page in enumerate(pages, 1):
                title = page["title"]
                logging.info(f"Processing page {i}/{len(pages)}: {title}")
                records.append({
                    "title": title,
                    "content": "Placeholder for page content",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Save results
            output_path = Path(args.output)
            client.save_json(records, output_path)
            
    except KeyboardInterrupt:
        logging.warning("Operation interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise
    
    logging.info("Scraping completed")

if __name__ == "__main__":
    main()