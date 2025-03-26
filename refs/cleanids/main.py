#!/usr/bin/env python3
"""
Script to clean JSON files in the /refs directory.
Removes unnecessary fields while preserving the data structure.
"""

import json
import os
import sys
from pathlib import Path

def clean_heroes_json(input_file, output_file=None):
    """
    Clean heroes.json file to keep only id, name, and displayName.
    
    Args:
        input_file (str or Path): Path to the input heroes.json file
        output_file (str or Path, optional): Path to the output file. If None, a new file with
                                            '_cleaned' suffix will be created in the same directory.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        input_path = Path(input_file)
        
        # Read the input file
        with open(input_path, 'r', encoding='utf-8') as f:
            heroes_data = json.load(f)
        
        # Verify the structure is a list
        if not isinstance(heroes_data, list):
            print(f"Error: {input_path} is not in the expected format (list of heroes)")
            return False
        
        # Clean the data
        cleaned_heroes = []
        for hero in heroes_data:
            cleaned_hero = {
                'id': hero.get('hero_id'),
                'name': hero.get('npc'),
                'displayName': hero.get('displayName')
            }
            cleaned_heroes.append(cleaned_hero)
        
        # Determine output path
        if output_file:
            output_path = Path(output_file)
        else:
            # Create a new file in the same directory with '_cleaned' suffix
            output_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the cleaned data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_heroes, f, indent=2)
            
        print(f"Successfully cleaned heroes data and saved to {output_path}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {input_path}: {str(e)}")
        return False
    except PermissionError:
        print(f"Permission denied when accessing {input_path}")
        return False
    except Exception as e:
        print(f"Error cleaning heroes data: {str(e)}")
        return False

def clean_items_json(input_file, output_file=None):
    """
    Clean items.json file to keep only id, name, displayName, shortName, price, and category.
    
    Args:
        input_file (str or Path): Path to the input items.json file
        output_file (str or Path, optional): Path to the output file. If None, a new file with
                                           '_cleaned' suffix will be created in the same directory.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        input_path = Path(input_file)
        
        # Read the input file
        with open(input_path, 'r', encoding='utf-8') as f:
            items_data = json.load(f)
        
        # Verify the structure is a dictionary
        if not isinstance(items_data, dict):
            print(f"Error: {input_path} is not in the expected format (dictionary of items)")
            return False
        
        # Clean the data
        cleaned_items = {}
        for item_id, item in items_data.items():
            cleaned_item = {
                'id': item.get('item_id'),
                'name': item.get('name'),
                'displayName': item.get('displayName'),
                'shortName': item.get('shortName')
            }
            
            # Add price if it exists
            if 'price' in item:
                cleaned_item['price'] = item['price']
            
            # Add neutral_item_tier (category) if it exists
            if 'neutral_item_tier' in item:
                cleaned_item['category'] = item['neutral_item_tier']
            
            cleaned_items[item_id] = cleaned_item
        
        # Determine output path
        if output_file:
            output_path = Path(output_file)
        else:
            # Create a new file in the same directory with '_cleaned' suffix
            output_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the cleaned data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_items, f, indent=2)
            
        print(f"Successfully cleaned items data and saved to {output_path}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {input_path}: {str(e)}")
        return False
    except PermissionError:
        print(f"Permission denied when accessing {input_path}")
        return False
    except Exception as e:
        print(f"Error cleaning items data: {str(e)}")
        return False

def main():
    """Main function to clean the JSON files in the refs directory."""
    # Define paths
    refs_dir = Path('refs')
    
    # Hero data
    heroes_file = '/Volumes/LNX/NEW/data2/refs/heroes.json'
    heroes_output = '/Volumes/LNX/NEW/data2/refs/heroes_cleaned.json'
    # Item data
    items_file = '/Volumes/LNX/NEW/data2/refs/items.json'
    items_output = '/Volumes/LNX/NEW/data2/refs/items_cleaned.json'
    
    # Process heroes file

    clean_heroes_json(heroes_file, heroes_output)
    
    # Process items file
    
    clean_items_json(items_file, items_output)

if __name__ == "__main__":
    main()