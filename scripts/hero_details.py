#!/usr/bin/env python3
"""
Dota 2 Hero Details Scraper (Stage 2)

This script uses the hero URLs from Stage 1 to scrape detailed information from each hero's page.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from datetime import datetime
import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dota2_hero_details_scraper')

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

def extract_abilities(soup):
    """
    Extract hero abilities from the page.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        list: List of ability dictionaries
    """
    abilities = []
    
    # Look for ability sections/tables
    ability_sections = soup.select('.ability, .abilities, div[id*="abilities"], div[id*="Abilities"]')
    
    # If specific sections not found, try to find tables
    if not ability_sections:
        ability_sections = soup.select('table.wikitable')
    
    for section in ability_sections:
        # Look for ability entries
        ability_entries = section.select('.ability-background, .ability-data, tr')
        
        for entry in ability_entries:
            # Skip if this doesn't look like an ability entry
            if not entry.select('th') and not entry.select('.ability-name') and not entry.select('b'):
                continue
            
            # Try to extract ability name
            ability_name = None
            
            # Try several potential selectors for ability name
            for selector in ['.ability-name', 'th', 'b', 'strong', 'h3', 'h4']:
                name_elem = entry.select_one(selector)
                if name_elem:
                    ability_name = name_elem.get_text(strip=True)
                    break
            
            # Skip if no name found
            if not ability_name:
                continue
            
            # Extract ability description
            description = ""
            
            # Try different potential description elements
            desc_elem = entry.select_one('.ability-description, td:nth-of-type(2), div.description, .mw-parser-output > p')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Look for ability stats
            ability_stats = {}
            
            # Try to find cooldown
            cooldown_elem = entry.select_one('span[title*="Cooldown"], span:contains("Cooldown"), td:contains("Cooldown")')
            if cooldown_elem:
                cooldown_text = cooldown_elem.get_text(strip=True)
                cooldown_match = re.search(r'Cooldown:?\s*(\d+\.?\d*)', cooldown_text, re.IGNORECASE)
                if cooldown_match:
                    ability_stats['cooldown'] = float(cooldown_match.group(1))
            
            # Try to find mana cost
            mana_elem = entry.select_one('span[title*="Mana"], span:contains("Mana"), td:contains("Mana")')
            if mana_elem:
                mana_text = mana_elem.get_text(strip=True)
                mana_match = re.search(r'Mana:?\s*(\d+\.?\d*)', mana_text, re.IGNORECASE)
                if mana_match:
                    ability_stats['mana_cost'] = float(mana_match.group(1))
            
            # Create ability dictionary
            ability = {
                "name": ability_name,
                "description": description
            }
            
            # Add stats if found
            if ability_stats:
                ability["stats"] = ability_stats
            
            # Look for ability image
            img_elem = entry.select_one('img')
            if img_elem and img_elem.get('src'):
                img_src = img_elem.get('src')
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                ability["image_url"] = img_src
            
            # Add to abilities list
            abilities.append(ability)
    
    # If we didn't find abilities through structured elements, try a more general approach
    if not abilities:
        # Look for sections that might contain abilities
        potential_sections = soup.select('h2, h3')
        
        for section in potential_sections:
            section_text = section.get_text(strip=True).lower()
            
            # Check if this section might be about abilities
            if 'abilities' in section_text or 'skills' in section_text or 'spells' in section_text:
                # Look at the next elements until the next section
                elem = section.next_sibling
                
                while elem and elem.name not in ['h2', 'h3']:
                    # Check if this element contains ability information
                    if elem.name in ['p', 'div'] and elem.get_text(strip=True):
                        text = elem.get_text(strip=True)
                        
                        # Try to identify ability names (often in bold or as standalone paragraphs)
                        if elem.name == 'p' and (elem.select('b') or len(text) < 50):
                            ability_name = text
                            
                            # Try to get the description from the next element
                            desc_elem = elem.next_sibling
                            description = ""
                            
                            if desc_elem and desc_elem.name == 'p':
                                description = desc_elem.get_text(strip=True)
                            
                            abilities.append({
                                "name": ability_name,
                                "description": description
                            })
                    
                    # Move to the next element
                    elem = elem.next_sibling
    
    return abilities

def extract_attributes(soup):
    """
    Extract hero attributes and statistics.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        dict: Hero attributes
    """
    attributes = {}
    
    # Try to find the infobox or attribute table
    infobox = soup.select_one('.infobox, .infobox-hero, .infobox-cell-2')
    
    if infobox:
        # Extract rows or key-value pairs
        rows = infobox.select('tr')
        
        for row in rows:
            # Skip rows without both header and data
            if not row.select('th') or not row.select('td'):
                continue
            
            # Get the attribute name and value
            attr_name = row.select_one('th').get_text(strip=True)
            attr_value = row.select_one('td').get_text(strip=True)
            
            # Skip empty values
            if not attr_value:
                continue
            
            # Clean up the attribute name
            attr_name = attr_name.lower().replace(':', '').replace(' ', '_')
            
            # Add to attributes
            attributes[attr_name] = attr_value
    
    # Look for specific attribute sections
    attr_sections = [
        ('primary_attribute', ['Primary Attribute', 'Attribute']),
        ('attack_type', ['Attack Type', 'Attack']),
        ('roles', ['Roles', 'Role', 'Position']),
        ('strength', ['Strength', 'STR']),
        ('agility', ['Agility', 'AGI']),
        ('intelligence', ['Intelligence', 'INT']),
        ('health', ['Health', 'HP']),
        ('mana', ['Mana', 'MP']),
        ('damage', ['Damage', 'ATK']),
        ('armor', ['Armor', 'DEF']),
        ('movement_speed', ['Movement Speed', 'Speed']),
    ]
    
    for attr_key, search_terms in attr_sections:
        if attr_key not in attributes:
            for term in search_terms:
                # Look for elements containing this term
                elems = soup.select(f'span:contains("{term}"), div:contains("{term}"), td:contains("{term}")')
                
                for elem in elems:
                    text = elem.get_text(strip=True)
                    
                    # Check if this looks like an attribute label
                    if term in text and ':' in text:
                        # Extract the value after the colon
                        value_match = re.search(f'{term}:?\\s*(.+)', text, re.IGNORECASE)
                        if value_match:
                            attributes[attr_key] = value_match.group(1).strip()
                            break
    
    return attributes

def extract_lore(soup):
    """
    Extract hero lore and background story.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        str: Hero lore
    """
    lore = ""
    
    # Try to find lore sections
    lore_sections = soup.select('div[id*="Lore"], div[id*="Background"], div[id*="Story"]')
    
    if lore_sections:
        for section in lore_sections:
            # Get all paragraphs in this section
            paragraphs = section.select('p')
            
            for p in paragraphs:
                if p.get_text(strip=True):
                    lore += p.get_text(strip=True) + "\n\n"
    
    # If no dedicated lore section, try to find potential lore paragraphs
    if not lore:
        # Look for sections that might contain lore
        potential_sections = soup.select('h2, h3')
        
        for section in potential_sections:
            section_text = section.get_text(strip=True).lower()
            
            # Check if this section might be about lore
            if any(term in section_text for term in ['lore', 'background', 'story', 'history']):
                # Look at the next elements until the next section
                elem = section.next_sibling
                
                while elem and elem.name not in ['h2', 'h3']:
                    # Check if this is a paragraph with text
                    if elem.name == 'p' and elem.get_text(strip=True):
                        lore += elem.get_text(strip=True) + "\n\n"
                    
                    # Move to the next element
                    elem = elem.next_sibling
    
    return lore.strip()

def scrape_hero_details(hero_url, hero_name=None):
    """
    Scrape detailed information about a hero from their individual page.
    
    Args:
        hero_url (str): URL of the hero page
        hero_name (str, optional): Name of the hero (if known)
        
    Returns:
        dict: Detailed hero information
    """
    # Set a user agent to identify the scraper
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Dota2HeroDetailsScraper/1.0; Python/3.x)'
    }
    
    result = {
        "status": "error",
        "error_type": "unknown",
        "message": "An unknown error occurred",
        "url": hero_url,
        "scraped_at": datetime.now().isoformat()
    }
    
    try:
        # Add a delay to be respectful to the server
        time.sleep(1)
        
        logger.info(f"Fetching hero details from {hero_url}")
        # Fetch the page content
        response = requests.get(hero_url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # If hero name wasn't provided, try to extract it from the page
        if not hero_name:
            # Try to get from page title
            title_elem = soup.select_one('h1.firstHeading')
            if title_elem:
                hero_name = title_elem.get_text(strip=True)
        
        # Get hero attributes
        attributes = extract_attributes(soup)
        
        # Get hero abilities
        abilities = extract_abilities(soup)
        
        # Get hero lore
        lore = extract_lore(soup)
        
        # Create hero details dictionary
        hero_details = {
            "name": hero_name,
            "url": hero_url
        }
        
        # Add attributes if found
        if attributes:
            hero_details["attributes"] = attributes
        
        # Add abilities if found
        if abilities:
            hero_details["abilities"] = abilities
        
        # Add lore if found
        if lore:
            hero_details["lore"] = lore
        
        # Try to get hero image
        hero_img = soup.select_one('.infobox-image img, .infobox img, .hero-infobox img')
        if hero_img and hero_img.get('src'):
            img_src = hero_img.get('src')
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            hero_details["image_url"] = img_src
        
        # Create the final result
        result = {
            "status": "success",
            "source": "Liquipedia Dota 2 Hero Details",
            "url": hero_url,
            "scraped_at": datetime.now().isoformat(),
            "hero": hero_details
        }
        
        return result
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {hero_url}: {str(e)}")
        return {
            "status": "error",
            "error_type": "request_error",
            "message": str(e),
            "url": hero_url,
            "scraped_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected error for {hero_url}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(e),
            "url": hero_url,
            "scraped_at": datetime.now().isoformat()
        }

def load_heroes_from_stage1(filename=None):
    """
    Load heroes data from Stage 1 output.
    
    Args:
        filename (str, optional): Path to the Stage 1 output file
        
    Returns:
        list: List of heroes with URLs
    """
    # If no filename provided, try to find the most recent output
    if not filename:
        # Look for files matching the pattern
        import glob
        files = glob.glob('dota2_heroes_portal_*.json')
        
        if not files:
            logger.error("No Stage 1 output files found")
            return []
        
        # Get the most recent file
        filename = max(files, key=os.path.getctime)
        logger.info(f"Using most recent Stage 1 output: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if data.get("status") == "success" and "heroes" in data:
            return data["heroes"]
        else:
            logger.error(f"Invalid data format in {filename}")
            return []
    
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading Stage 1 data: {str(e)}")
        return []

def scrape_all_hero_details(heroes, max_workers=5, cache_dir='hero_cache'):
    """
    Scrape details for all heroes and combine into a single dataset.
    
    Args:
        heroes (list): List of heroes with URLs from Stage 1
        max_workers (int): Maximum number of concurrent workers
        cache_dir (str): Directory for caching hero details
        
    Returns:
        dict: Combined dataset with all hero details
    """
    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)
    
    all_heroes = []
    errors = []
    
    # Function to process a single hero with caching
    def process_hero(hero):
        hero_name = hero['name']
        hero_url = hero['url']
        
        # Create a cache filename based on the hero name
        cache_file = os.path.join(cache_dir, f"{re.sub(r'[^\w]', '_', hero_name)}.json")
        
        # Check if we have a cached result
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    logger.info(f"Loaded cached data for {hero_name}")
                    return result
            except (json.JSONDecodeError, FileNotFoundError):
                logger.warning(f"Invalid cache file for {hero_name}, scraping fresh data")
        
        # Scrape hero details
        result = scrape_hero_details(hero_url, hero_name)
        
        # Cache the result if successful
        if result.get("status") == "success":
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result
    
    # Use ThreadPoolExecutor to scrape multiple heroes concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_hero = {executor.submit(process_hero, hero): hero for hero in heroes}
        
        # Process results as they complete
        for future in as_completed(future_to_hero):
            hero = future_to_hero[future]
            try:
                result = future.result()
                
                if result.get("status") == "success":
                    all_heroes.append(result.get("hero"))
                    logger.info(f"Successfully scraped {hero['name']}")
                else:
                    errors.append({
                        "hero": hero['name'],
                        "url": hero['url'],
                        "error": result.get("message")
                    })
                    logger.error(f"Failed to scrape {hero['name']}: {result.get('message')}")
            
            except Exception as e:
                errors.append({
                    "hero": hero['name'],
                    "url": hero['url'],
                    "error": str(e)
                })
                logger.error(f"Exception while processing {hero['name']}: {str(e)}")
    
    # Create the final dataset
    dataset = {
        "status": "success" if all_heroes else "error",
        "source": "Liquipedia Dota 2 Heroes",
        "scraped_at": datetime.now().isoformat(),
        "hero_count": len(all_heroes),
        "heroes": all_heroes
    }
    
    # Include errors if any
    if errors:
        dataset["errors"] = errors
        dataset["error_count"] = len(errors)
    
    return dataset

def main():
    """
    Main function to run the Stage 2 scraper.
    """
    print("Starting Dota 2 Hero Details scraper (Stage 2)...")
    
    # Load heroes from Stage 1
    heroes = load_heroes_from_stage1()
    
    if not heroes:
        print("No heroes found from Stage 1. Please run the Stage 1 scraper first.")
        return
    
    print(f"Loaded {len(heroes)} heroes from Stage 1")
    
    # Ask user if they want to scrape all heroes or limit to a few for testing
    limit = input("Enter number of heroes to scrape (or press Enter for all): ")
    
    if limit and limit.isdigit():
        limit = int(limit)
        heroes = heroes[:limit]
        print(f"Limiting to {limit} heroes for testing")
    
    # Ask for max concurrent workers
    max_workers = input("Enter maximum concurrent workers (default: 5): ")
    
    if max_workers and max_workers.isdigit():
        max_workers = int(max_workers)
    else:
        max_workers = 5
    
    print(f"Using {max_workers} concurrent workers")
    
    # Scrape all hero details
    print(f"Scraping details for {len(heroes)} heroes...")
    dataset = scrape_all_hero_details(heroes, max_workers)
    
    # Save the results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'dota2_hero_details_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    # Report results
    if dataset.get("status") == "success":
        print(f"Scraping complete. Successfully scraped {dataset.get('hero_count', 0)} heroes.")
        if dataset.get("errors"):
            print(f"Errors encountered for {dataset.get('error_count', 0)} heroes.")
    else:
        print("Scraping failed. No heroes were successfully scraped.")
    
    print(f"Results saved to '{output_file}'")

def run_complete_pipeline():
    """
    Run the complete two-stage scraping pipeline.
    """
    print("Starting complete Dota 2 Heroes scraping pipeline...")
    
    # Stage 1: Scrape heroes portal
    print("\n=== STAGE 1: Heroes Portal Scraping ===\n")
    stage1_result = scrape_with_cache(url='https://liquipedia.net/dota2/Portal:Heroes')
    
    if stage1_result.get("status") != "success":
        print(f"Stage 1 failed: {stage1_result.get('message')}")
        return
    
    heroes = stage1_result.get("heroes", [])
    print(f"Stage 1 complete. Found {len(heroes)} heroes.")
    
    # Stage 2: Scrape hero details
    print("\n=== STAGE 2: Hero Details Scraping ===\n")
    
    # Ask user if they want to scrape all heroes or limit to a few for testing
    limit = input("Enter number of heroes to scrape (or press Enter for all): ")
    
    if limit and limit.isdigit():
        limit = int(limit)
        heroes = heroes[:limit]
        print(f"Limiting to {limit} heroes for testing")
    
    # Ask for max concurrent workers
    max_workers = input("Enter maximum concurrent workers (default: 5): ")
    
    if max_workers and max_workers.isdigit():
        max_workers = int(max_workers)
    else:
        max_workers = 5
    
    print(f"Using {max_workers} concurrent workers")
    
    # Scrape all hero details
    print(f"Scraping details for {len(heroes)} heroes...")
    dataset = scrape_all_hero_details(heroes, max_workers)
    
    # Save the results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'dota2_complete_heroes_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    # Report results
    if dataset.get("status") == "success":
        print(f"Complete pipeline finished. Successfully scraped {dataset.get('hero_count', 0)} heroes.")
        if dataset.get("errors"):
            print(f"Errors encountered for {dataset.get('error_count', 0)} heroes.")
    else:
        print("Pipeline failed. No heroes were successfully scraped.")
    
    print(f"Final results saved to '{output_file}'")

if __name__ == "__main__":
    # Determine which mode to run in
    mode = input("Run mode: (1) Stage 2 only, (2) Complete pipeline: ")
    
    if mode == "2":
        run_complete_pipeline()
    else:
        main()