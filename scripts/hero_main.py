#!/usr/bin/env python3
"""
Dota 2 Heroes Portal Scraper (Stage 1)

This script scrapes the Dota 2 Heroes Portal page to extract all heroes and their URLs.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
import logging
import urllib.parse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dota2_heroes_portal_scraper')

def scrape_heroes_portal(url='https://liquipedia.net/dota2/Portal:Heroes'):
    """
    Scrape the Dota 2 Heroes Portal page to get all heroes and their URLs.
    
    Args:
        url (str): URL of the heroes portal
        
    Returns:
        dict: Structured data containing heroes and their URLs
    """
    # Set a user agent to identify the scraper
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Dota2HeroesPortalScraper/1.0; Python/3.x)'
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
        
        logger.info(f"Fetching heroes portal from {url}")
        # Fetch the page content
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize data structures
        heroes = []
        warnings = []
        
        # Look for different possible hero listing formats
        
        # Try to find hero galleries or grids first (most common format)
        hero_galleries = soup.select('.herobox, .gallerybox, .heroicon, .hero-grid')
        
        if hero_galleries:
            logger.info(f"Found {len(hero_galleries)} hero entries in gallery/grid format")
            
            for hero_box in hero_galleries:
                # Look for the hero link - most likely in an <a> tag
                hero_link = hero_box.select_one('a')
                
                if not hero_link or not hero_link.get('href'):
                    continue
                
                href = hero_link.get('href')
                
                # Get the hero name - could be in title, alt or text
                hero_name = None
                
                # Try title attribute first
                if hero_link.get('title'):
                    hero_name = hero_link.get('title')
                
                # Then try to get from img alt
                if not hero_name and hero_link.select_one('img'):
                    hero_img = hero_link.select_one('img')
                    if hero_img.get('alt'):
                        hero_name = hero_img.get('alt')
                
                # Last resort, use text
                if not hero_name:
                    hero_name = hero_link.get_text(strip=True)
                
                # Skip if we couldn't extract a hero name
                if not hero_name:
                    continue
                
                # Clean up the name and URL
                hero_name = hero_name.strip()
                
                # Handle relative URLs
                if href.startswith('/'):
                    href = 'https://liquipedia.net' + href
                else:
                    href = urllib.parse.urljoin(url, href)
                
                # Add to the heroes list
                heroes.append({
                    "name": hero_name,
                    "url": href
                })
        
        # If no hero galleries found, try tables
        if not heroes:
            logger.info("No heroes found in gallery/grid format, trying tables")
            
            # Look for tables that might contain hero listings
            hero_tables = soup.select('table.wikitable, table.sortable, table.roster')
            
            for table in hero_tables:
                # Get all rows except the header
                rows = table.select('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.select('td')
                    
                    # Skip rows with no cells
                    if not cells:
                        continue
                    
                    # Look for links in cells
                    for cell in cells:
                        links = cell.select('a')
                        
                        for link in links:
                            if not link.get('href'):
                                continue
                            
                            href = link.get('href')
                            
                            # Skip links that are unlikely to be hero pages
                            if any(skip in href.lower() for skip in [
                                'category:', 'template:', 'file:', 'user:', 'talk:', 'special:'
                            ]):
                                continue
                            
                            # Get hero name
                            hero_name = None
                            
                            if link.get('title'):
                                hero_name = link.get('title')
                            else:
                                hero_name = link.get_text(strip=True)
                            
                            # Skip if no name
                            if not hero_name:
                                continue
                            
                            # Clean up the name and URL
                            hero_name = hero_name.strip()
                            
                            # Handle relative URLs
                            if href.startswith('/'):
                                href = 'https://liquipedia.net' + href
                            else:
                                href = urllib.parse.urljoin(url, href)
                            
                            # Add to the heroes list if it looks like a hero page
                            if '/dota2/' in href.lower() and not href.endswith(('/Portal:Heroes', '/Heroes')):
                                heroes.append({
                                    "name": hero_name,
                                    "url": href
                                })
        
        # If still no heroes found, try a more general approach
        if not heroes:
            logger.info("No heroes found in tables, trying general link search")
            
            # Look for content divs that might contain hero links
            content_divs = soup.select('.mw-parser-output, .hero-list, #mw-content-text')
            
            for div in content_divs:
                # Look for links
                links = div.select('a')
                
                for link in links:
                    if not link.get('href'):
                        continue
                    
                    href = link.get('href')
                    
                    # Skip links that are unlikely to be hero pages
                    if any(skip in href.lower() for skip in [
                        'category:', 'template:', 'file:', 'user:', 'talk:', 'special:', 'portal:'
                    ]):
                        continue
                    
                    # Get hero name
                    hero_name = None
                    
                    if link.get('title'):
                        hero_name = link.get('title')
                    else:
                        hero_name = link.get_text(strip=True)
                    
                    # Skip if no name
                    if not hero_name:
                        continue
                    
                    # Clean up the name and URL
                    hero_name = hero_name.strip()
                    
                    # Handle relative URLs
                    if href.startswith('/'):
                        href = 'https://liquipedia.net' + href
                    else:
                        href = urllib.parse.urljoin(url, href)
                    
                    # Add to the heroes list if it looks like a hero page (direct /dota2/{HeroName} format)
                    path_parts = urllib.parse.urlparse(href).path.split('/')
                    if '/dota2/' in href.lower() and len(path_parts) >= 3 and path_parts[-2] == 'dota2':
                        heroes.append({
                            "name": hero_name,
                            "url": href
                        })
        
        # Remove duplicates by converting to a dictionary with URL as key
        heroes_dict = {hero['url']: hero for hero in heroes}
        unique_heroes = list(heroes_dict.values())
        
        # Sort heroes by name
        unique_heroes.sort(key=lambda x: x['name'])
        
        # Create the final JSON structure
        result = {
            "status": "success",
            "source": "Liquipedia Dota 2 Heroes Portal",
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "hero_count": len(unique_heroes),
            "heroes": unique_heroes
        }
        
        # Include warnings if any heroes were skipped
        if len(heroes) != len(unique_heroes):
            warning = f"Found {len(heroes)} heroes but {len(heroes) - len(unique_heroes)} were duplicates"
            warnings.append(warning)
            logger.warning(warning)
        
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

def scrape_with_cache(url='https://liquipedia.net/dota2/Portal:Heroes', 
                      cache_file='dota2_heroes_portal_cache.json', 
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
    result = scrape_heroes_portal(url)
    
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
    print("Starting Dota 2 Heroes Portal scraper...")
    
    # Use cached results if available and not expired
    result = scrape_with_cache()
    
    # Pretty print the JSON output
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to a file with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'dota2_heroes_portal_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Report results
    if result.get("status") == "success":
        print(f"Scraping complete. Found {result.get('hero_count', 0)} heroes.")
        if result.get("warnings"):
            print(f"Warnings: {len(result.get('warnings'))}")
    else:
        print(f"Scraping failed: {result.get('message')}")
        
    print(f"Results saved to '{output_file}'")

if __name__ == "__main__":
    main()