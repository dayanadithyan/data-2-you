#!/usr/bin/env python3
"""
Dota 2 Hero Attributes Scraper

This script scrapes hero attribute data from Liquipedia and structures it as JSON.
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
logger = logging.getLogger('dota2_scraper')

def safe_parse_float(text):
    """
    Safely parse a string to float, handling various formats.
    
    Args:
        text (str): Text to parse
        
    Returns:
        float or None: Parsed float value or None if parsing failed
    """
    if not text:
        return None
        
    try:
        text = str(text).strip()
        # Find all decimal numbers (including negatives) using a more precise regex
        matches = re.findall(r'-?\d+\.?\d*', text)
        return float(matches[0]) if matches else None
    except (IndexError, ValueError, TypeError):
        return None

def find_hero_table(soup):
    """
    Find the hero attributes table in the page.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        BeautifulSoup or None: The hero table element or None if not found
    """
    # Try to find table with specific header content first
    tables = soup.select('table.wikitable')
    
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.select('tr:first-child th')]
        # Check if this looks like the hero attributes table by examining headers
        if len(headers) >= 5 and 'Hero' in headers and any('Attribute' in h for h in headers):
            return table
            
    # Fallback: just take the first wikitable if we couldn't find a match
    return tables[0] if tables else None

def scrape_dota2_heroes(url='https://liquipedia.net/dota2/Table_of_hero_attributes'):
    """
    Scrape Dota 2 hero attributes from Liquipedia.
    
    Args:
        url (str): URL to scrape
        
    Returns:
        dict: Structured data containing hero attributes
    """
    # Set a user agent to identify the scraper
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Dota2HeroScraper/1.0; Python/3.x)'
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
        
        # Find the hero attribute table
        table = find_hero_table(soup)
        if not table:
            return {
                "status": "error",
                "error_type": "table_not_found",
                "message": "Could not find hero attributes table",
                "scraped_at": datetime.now().isoformat()
            }
        
        # Check if we have table rows
        rows = table.select('tr')
        if len(rows) <= 1:
            return {
                "status": "error",
                "error_type": "empty_table",
                "message": "Table has insufficient rows",
                "scraped_at": datetime.now().isoformat()
            }
        
        # Process each row in the table
        heroes = []
        warnings = []
        
        # Skip the header row
        header_row = rows[0]
        header_texts = [th.get_text(strip=True) for th in header_row.select('th')]
        
        # Map column indexes based on headers
        col_map = {
            'name': next((i for i, h in enumerate(header_texts) if 'Hero' in h), 0),
            'primary_attr': next((i for i, h in enumerate(header_texts) if 'Primary' in h and 'Attribute' in h), 1),
            'str_base': next((i for i, h in enumerate(header_texts) if 'Str' in h and 'Base' in h), 2),
            'str_gain': next((i for i, h in enumerate(header_texts) if 'Str' in h and 'Gain' in h), 3),
            'agi_base': next((i for i, h in enumerate(header_texts) if 'Agi' in h and 'Base' in h), 4),
            'agi_gain': next((i for i, h in enumerate(header_texts) if 'Agi' in h and 'Gain' in h), 5),
            'int_base': next((i for i, h in enumerate(header_texts) if 'Int' in h and 'Base' in h), 6),
            'int_gain': next((i for i, h in enumerate(header_texts) if 'Int' in h and 'Gain' in h), 7),
            'attack_type': next((i for i, h in enumerate(header_texts) if 'Attack' in h), 8),
            'complexity': next((i for i, h in enumerate(header_texts) if 'Complex' in h), 9),
        }
        
        logger.info(f"Found {len(rows)-1} heroes to process")
        
        for row in rows[1:]:  # Skip header row
            columns = row.select('td')
            
            # Skip rows with insufficient columns
            if len(columns) <= max(col_map.values()):
                continue
                
            # Extract hero name
            hero_name = columns[col_map['name']].get_text(strip=True)
            
            # Skip empty rows
            if not hero_name:
                continue
                
            # Extract primary attribute
            primary_attribute = columns[col_map['primary_attr']].get_text(strip=True)
            
            # Extract numeric values with validation
            str_base = safe_parse_float(columns[col_map['str_base']].get_text())
            str_gain = safe_parse_float(columns[col_map['str_gain']].get_text())
            agi_base = safe_parse_float(columns[col_map['agi_base']].get_text())
            agi_gain = safe_parse_float(columns[col_map['agi_gain']].get_text())
            int_base = safe_parse_float(columns[col_map['int_base']].get_text())
            int_gain = safe_parse_float(columns[col_map['int_gain']].get_text())
            
            # Create hero object
            hero = {
                "name": hero_name,
                "primary_attribute": primary_attribute,
                "strength": {
                    "base": str_base,
                    "gain": str_gain
                },
                "agility": {
                    "base": agi_base,
                    "gain": agi_gain
                },
                "intelligence": {
                    "base": int_base,
                    "gain": int_gain
                },
                "attack_type": columns[col_map['attack_type']].get_text(strip=True),
                "complexity": columns[col_map['complexity']].get_text(strip=True)
            }
            
            # Check for data completeness
            if None in [str_base, str_gain, agi_base, agi_gain, int_base, int_gain]:
                warning = f"Incomplete data for hero {hero_name}"
                warnings.append(warning)
                logger.warning(warning)
            
            # Add the hero to our list
            heroes.append(hero)
        
        # Create the final JSON structure
        result = {
            "status": "success",
            "source": "Liquipedia Dota 2 Hero Attributes",
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "hero_count": len(heroes),
            "heroes": heroes
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

def scrape_with_cache(url='https://liquipedia.net/dota2/Table_of_hero_attributes', 
                      cache_file='dota2_cache.json', 
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
    result = scrape_dota2_heroes(url)
    
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
    print("Starting Dota 2 hero attributes scraper...")
    
    # Use cached results if available and not expired
    result = scrape_with_cache()
    
    # Pretty print the JSON output
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to a file with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'dota2_heroes_{timestamp}.json'
    
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