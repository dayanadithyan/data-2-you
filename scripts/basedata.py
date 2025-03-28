#!/usr/bin/env python3
"""
Dota 2 Hero Introductions Scraper

This script scrapes hero introduction data from Liquipedia and structures it as JSON.
Includes error handling, caching, and robust data processing.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dota2_introductions_scraper')

def extract_date(text):
    """
    Extract a date from text.
    Different date formats might be used on the page.
    
    Args:
        text (str): Text containing a date
        
    Returns:
        str or None: Extracted date or None if not found
    """
    if not text:
        return None
        
    # Try different date formats
    # Format: "November 1, 2010" or "June 24, 2015"
    date_match = re.search(r'(?:\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b)', text)
    if date_match:
        return date_match.group(0)
    
    # ISO format: "2010-11-01" or "2015-06-24"
    iso_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', text)
    if iso_match:
        return iso_match.group(0)
    
    # Simple year: "2010" or "2015"
    year_match = re.search(r'\b\d{4}\b', text)
    if year_match:
        return year_match.group(0)
        
    return None

def extract_patch(text):
    """
    Extract patch information from text.
    
    Args:
        text (str): Text containing patch info
        
    Returns:
        str or None: Extracted patch info or None if not found
    """
    if not text:
        return None
        
    # Look for patterns like "Patch 6.72" or "7.00"
    patch_match = re.search(r'(?:Patch\s+)?(\d+\.\d+[a-z]?)', text, re.IGNORECASE)
    if patch_match:
        patch = patch_match.group(0)
        # If "Patch" is not in the match but was in the text, add it
        if "patch" not in patch.lower() and "patch" in text.lower():
            return f"Patch {patch_match.group(1)}"
        return patch
        
    return None

def extract_event(text):
    """
    Extract event information from text.
    
    Args:
        text (str): Text containing event info
        
    Returns:
        str or None: Extracted event info or None if not found
    """
    if not text:
        return None
        
    # Common event formats and markers
    event_markers = [
        "International", "TI", "Major", "Update",
        "Frostivus", "Diretide", "New Bloom",
        "Dueling Fates", "Nemestice", "Aghanim",
        "Beta", "Official Release"
    ]
    
    for marker in event_markers:
        if marker.lower() in text.lower():
            # Try to extract the full event name
            event_match = re.search(fr'(?:\w+\s+)?{marker}(?:\s+\w+)?', text, re.IGNORECASE)
            if event_match:
                return event_match.group(0).strip()
    
    return None

def scrape_dota2_hero_introductions(url='https://liquipedia.net/dota2/Heroes/Introductions'):
    """
    Scrape Dota 2 hero introductions from Liquipedia.
    
    Args:
        url (str): URL to scrape
        
    Returns:
        dict: Structured data containing hero introductions
    """
    # Set a user agent to identify the scraper
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Dota2IntroductionsScraper/1.0; Python/3.x)'
    }
    
    result = {
        "status": "error",
        "error_type": "unknown",
        "message": "An unknown error occurred",
        "scraped_at": datetime.now().isoformat()
    }
    
    try:
        # Add a small delay to be respectful to the server
        time.sleep(1)
        
        logger.info(f"Fetching data from {url}")
        # Fetch the page content
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # The page structure might have tables, sections, or other formats
        # We'll try to handle different possibilities
        
        hero_introductions = []
        warnings = []
        
        # Check for tables first
        tables = soup.select('table.wikitable')
        
        if tables:
            # Process tables
            for table in tables:
                headers = [th.get_text(strip=True) for th in table.select('tr:first-child th')]
                
                # Skip tables that don't look like hero introduction tables
                if not headers or not any('Hero' in h for h in headers):
                    continue
                
                # Map columns based on headers
                col_map = {
                    'hero': next((i for i, h in enumerate(headers) if 'Hero' in h), None),
                    'date': next((i for i, h in enumerate(headers) if any(term in h for term in ['Date', 'Added', 'Introduction', 'Released'])), None),
                    'patch': next((i for i, h in enumerate(headers) if 'Patch' in h), None),
                    'event': next((i for i, h in enumerate(headers) if any(term in h for term in ['Event', 'Update', 'Occasion'])), None)
                }
                
                # Skip tables without a hero and date column
                if col_map['hero'] is None or col_map['date'] is None:
                    continue
                
                # Process rows
                for row in table.select('tr')[1:]:  # Skip header row
                    columns = row.select('td')
                    
                    # Skip rows with insufficient columns
                    if len(columns) <= max(filter(None, col_map.values())):
                        continue
                    
                    # Extract hero name (might contain an image or link)
                    hero_col = columns[col_map['hero']]
                    hero_name = None
                    
                    # Try to get name from a link
                    hero_link = hero_col.select_one('a')
                    if hero_link and hero_link.get('title'):
                        hero_name = hero_link.get('title')
                    
                    # If no link title, try the text content
                    if not hero_name:
                        hero_name = hero_col.get_text(strip=True)
                    
                    # Skip if we couldn't extract a hero name
                    if not hero_name:
                        continue
                    
                    # Extract date
                    date_col = columns[col_map['date']]
                    date_text = date_col.get_text(strip=True)
                    introduction_date = extract_date(date_text)
                    
                    # Extract patch if column exists
                    patch = None
                    if col_map['patch'] is not None:
                        patch_col = columns[col_map['patch']]
                        patch_text = patch_col.get_text(strip=True)
                        patch = extract_patch(patch_text)
                    
                    # Extract event if column exists
                    event = None
                    if col_map['event'] is not None:
                        event_col = columns[col_map['event']]
                        event_text = event_col.get_text(strip=True)
                        event = extract_event(event_text)
                    
                    # Create hero introduction entry
                    intro = {
                        "hero": hero_name,
                        "introduction_date": introduction_date
                    }
                    
                    # Add optional fields if available
                    if patch:
                        intro["patch"] = patch
                    if event:
                        intro["event"] = event
                    
                    # Check for data completeness
                    if not introduction_date:
                        warning = f"Incomplete data for hero {hero_name}: missing introduction date"
                        warnings.append(warning)
                        logger.warning(warning)
                    
                    # Add to the list
                    hero_introductions.append(intro)
        
        # If no tables found, try looking for sections or lists
        if not hero_introductions:
            # Try to find sections with hero introductions
            sections = soup.select('div.mw-parser-output > h2, div.mw-parser-output > h3')
            
            current_section = None
            
            for section in sections:
                section_title = section.get_text(strip=True)
                
                # Skip irrelevant sections
                if not any(term in section_title.lower() for term in ['heroes', 'introductions', 'releases', 'patches']):
                    continue
                
                current_section = section_title
                
                # Get the next elements until the next section
                element = section.next_sibling
                
                while element and (element.name not in ['h2', 'h3']):
                    # Check if it's a list item
                    if element.name == 'ul':
                        for li in element.select('li'):
                            text = li.get_text(strip=True)
                            
                            # Try to extract hero name, date, patch, and event
                            # This is trickier as the format is less structured
                            
                            # Look for hero names in links
                            hero_name = None
                            for link in li.select('a'):
                                if link.get('title') and 'Category:' not in link.get('title'):
                                    hero_name = link.get('title')
                                    break
                            
                            # If we found a hero name
                            if hero_name:
                                # Extract other information from the text
                                introduction_date = extract_date(text)
                                patch = extract_patch(text)
                                event = extract_event(text)
                                
                                # Create hero introduction entry
                                intro = {
                                    "hero": hero_name,
                                    "introduction_date": introduction_date,
                                    "section": current_section
                                }
                                
                                # Add optional fields if available
                                if patch:
                                    intro["patch"] = patch
                                if event:
                                    intro["event"] = event
                                
                                # Check for data completeness
                                if not introduction_date:
                                    warning = f"Incomplete data for hero {hero_name}: missing introduction date"
                                    warnings.append(warning)
                                    logger.warning(warning)
                                
                                # Add to the list
                                hero_introductions.append(intro)
                    
                    # Move to the next element
                    element = element.next_sibling
        
        # If still no data, try a more general approach
        if not hero_introductions:
            # Look for any lists with hero links
            for ul in soup.select('div.mw-parser-output ul'):
                for li in ul.select('li'):
                    text = li.get_text(strip=True)
                    
                    # Check if this list item might be about a hero introduction
                    if not any(term in text.lower() for term in ['hero', 'release', 'patch', 'introduc', 'added']):
                        continue
                    
                    # Look for hero names in links
                    hero_name = None
                    for link in li.select('a'):
                        if link.get('title') and 'Category:' not in link.get('title'):
                            hero_name = link.get('title')
                            break
                    
                    # If we found a hero name
                    if hero_name:
                        # Extract other information from the text
                        introduction_date = extract_date(text)
                        patch = extract_patch(text)
                        event = extract_event(text)
                        
                        # Create hero introduction entry
                        intro = {
                            "hero": hero_name,
                            "introduction_date": introduction_date
                        }
                        
                        # Add optional fields if available
                        if patch:
                            intro["patch"] = patch
                        if event:
                            intro["event"] = event
                        
                        # Check for data completeness
                        if not introduction_date:
                            warning = f"Incomplete data for hero {hero_name}: missing introduction date"
                            warnings.append(warning)
                            logger.warning(warning)
                        
                        # Add to the list
                        hero_introductions.append(intro)
        
        # Create the final JSON structure
        result = {
            "status": "success",
            "source": "Liquipedia Dota 2 Hero Introductions",
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "hero_count": len(hero_introductions),
            "introductions": hero_introductions
        }
        
        # Include warnings if any
        if warnings:
            result["warnings"] = warnings
            
        return result
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {
            "status": "error",
            "error_type": "request_error",
            "message": str(e),
            "scraped_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(e),
            "scraped_at": datetime.now().isoformat()
        }

def scrape_with_cache(url='https://liquipedia.net/dota2/Heroes/Introductions', 
                      cache_file='dota2_introductions_cache.json', 
                      cache_ttl=3600):
    """
    Scrape with a simple file-based cache.
    
    Args:
        url (str): URL to scrape
        cache_file (str): Path to cache file
        cache_ttl (int): Cache time-to-live in seconds
        
    Returns:
        dict: Scraped data
    """
    # Check if we have a valid cache file
    if os.path.exists(cache_file):
        cache_age = time.time() - os.path.getmtime(cache_file)
        if cache_age < cache_ttl:
            logger.info(f"Using cached data (age: {cache_age:.1f}s)")
            with open(cache_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Cache file is corrupt, scraping fresh data")
    
    # Scrape as normal
    result = scrape_dota2_hero_introductions(url)
    
    # Save to cache if successful
    if result.get("status") == "success":
        logger.info("Saving results to cache")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    return result

def main():
    """
    Main function to run the scraper and output the results.
    """
    print("Starting Dota 2 hero introductions scraper...")
    
    # Use cached results if available and not expired
    result = scrape_with_cache()
    
    # Pretty print the JSON output
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to a file with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'dota2_introductions_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Report results
    if result.get("status") == "success":
        print(f"Scraping complete. Found {result.get('hero_count', 0)} hero introductions.")
        if result.get("warnings"):
            print(f"Warnings: {len(result.get('warnings'))}")
    else:
        print(f"Scraping failed: {result.get('message')}")
        
    print(f"Results saved to '{output_file}'")

if __name__ == "__main__":
    main()