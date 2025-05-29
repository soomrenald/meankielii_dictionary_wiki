import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from datetime import datetime

def analyze_dictionary_website():
    base_url = "https://meankielensanakirja.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Get the main page
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get the custom script
        script_url = f"{base_url}/static/script.js"
        script_response = requests.get(script_url, headers=headers)
        script_response.raise_for_status()
        
        print("Analyzing custom script...")
        script_content = script_response.text
        
        # Look for potential API endpoints or data loading patterns
        if 'fetch' in script_content or 'ajax' in script_content:
            print("\nFound potential data loading patterns:")
            for line in script_content.split('\n'):
                if 'fetch' in line or 'ajax' in line or 'url' in line:
                    print(line.strip())
        
        # Look for any dictionary-related endpoints
        if 'dictionary' in script_content.lower() or 'word' in script_content.lower():
            print("\nFound potential dictionary-related code:")
            for line in script_content.split('\n'):
                if 'dictionary' in line.lower() or 'word' in line.lower():
                    print(line.strip())
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing the website: {e}")

def analyze_browse_page(page_num=1):
    url = f"https://meankielensanakirja.com/sv/advanced?page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"Analyzing browse page {page_num}...")
        # Print all anchor tags and their hrefs
        for a in soup.find_all('a', href=True):
            print(f"Anchor text: {a.text.strip()} | Href: {a['href']}")
    except requests.exceptions.RequestException as e:
        print(f"Error accessing the browse page: {e}")

def check_for_sitemap_or_data_dump():
    base_url = "https://meankielensanakirja.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    potential_paths = [
        "/sitemap.xml",
        "/data.json",
        "/export",
        "/download",
        "/api/export"
    ]
    for path in potential_paths:
        url = base_url + path
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print(f"Found potential data source: {url}")
        except requests.exceptions.RequestException as e:
            print(f"Error checking {url}: {e}")

def extract_word_ids_from_page(page_num):
    print(f"DEBUG: Starting to extract word IDs from page {page_num}")
    url = f"https://meankielensanakirja.com/sv/advanced?page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    word_ids = []
    try:
        print(f"DEBUG: Fetching page {page_num}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"DEBUG: Successfully fetched page {page_num}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"DEBUG: Parsed HTML for page {page_num}")
        
        # Look for word links
        word_links = soup.find_all('a', href=re.compile(r"/sv/sana/id/\d+/"))
        print(f"DEBUG: Found {len(word_links)} word links on page {page_num}")
        
        for link in word_links:
            word_id = re.search(r"/sv/sana/id/(\d+)/", link['href']).group(1)
            word_ids.append(word_id)
        
        print(f"Found {len(word_ids)} words on page {page_num}")
        return word_ids
    except requests.exceptions.RequestException as e:
        print(f"Error accessing page {page_num}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error on page {page_num}: {e}")
        return []

def fetch_word_data(word_id):
    print(f"DEBUG: Fetching data for word ID {word_id}")
    url = f"https://meankielensanakirja.com/sv/api/{word_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching word {word_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching word {word_id}: {e}")
        return None

def save_progress(dictionary_data, output_file):
    print(f"DEBUG: Saving progress to {output_file}")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(dictionary_data, f, ensure_ascii=False, indent=2)
        print(f"Progress saved to {output_file}")
    except Exception as e:
        print(f"Error saving progress: {e}")

def collect_word_ids():
    print("DEBUG: Starting collect_word_ids function")
    word_ids_file = "word_ids.json"
    
    # Check if we already have word IDs
    if os.path.exists(word_ids_file):
        print(f"Found existing word IDs file: {word_ids_file}")
        try:
            with open(word_ids_file, "r") as f:
                word_ids = json.load(f)
            print(f"Successfully loaded {len(word_ids)} word IDs from file")
            return word_ids
        except Exception as e:
            print(f"Error loading word IDs file: {e}")
            print("Will collect word IDs again")
    
    # If not, collect them
    print("No existing word IDs file found. Collecting word IDs...")
    all_word_ids = []
    total_pages = 445
    
    for page in range(1, total_pages + 1):
        word_ids = extract_word_ids_from_page(page)
        all_word_ids.extend(word_ids)
        time.sleep(1)  # Be nice to the server
        
        # Save progress every 10 pages
        if page % 10 == 0:
            print(f"Progress: {page}/{total_pages} pages processed")
            try:
                with open(word_ids_file, "w") as f:
                    json.dump(all_word_ids, f)
                print(f"Saved {len(all_word_ids)} word IDs to file")
            except Exception as e:
                print(f"Error saving word IDs: {e}")
    
    print(f"\nFound {len(all_word_ids)} total word IDs")
    return all_word_ids

def main():
    print("DEBUG: Starting main function")
    try:
        # Generate timestamp for the output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"dictionary_data_{timestamp}.json"
        print(f"DEBUG: Output file will be {output_file}")
        
        # First, get all word IDs
        word_ids = collect_word_ids()
        print(f"DEBUG: Collected {len(word_ids)} word IDs")
        
        # Load existing dictionary data if it exists
        dictionary_data = []
        if os.path.exists("dictionary_data.json"):
            print("Found existing dictionary data file. Loading...")
            try:
                with open("dictionary_data.json", "r", encoding="utf-8") as f:
                    dictionary_data = json.load(f)
                print(f"Loaded {len(dictionary_data)} existing entries")
            except Exception as e:
                print(f"Error loading existing dictionary data: {e}")
        
        # Get the IDs of words we've already processed
        processed_ids = {entry.get('id') for entry in dictionary_data if entry.get('id')}
        print(f"DEBUG: Found {len(processed_ids)} already processed words")
        
        # Fetch data for each word that hasn't been processed yet
        for i, word_id in enumerate(word_ids, 1):
            if word_id in processed_ids:
                print(f"Skipping already processed word {i}/{len(word_ids)} (ID: {word_id})...")
                continue
                
            print(f"Fetching data for word {i}/{len(word_ids)} (ID: {word_id})...")
            word_data = fetch_word_data(word_id)
            if word_data:
                dictionary_data.append(word_data)
            time.sleep(1)  # Be nice to the server
            
            # Save progress every 50 words
            if i % 50 == 0:
                print(f"Progress: {i}/{len(word_ids)} words processed")
                save_progress(dictionary_data, output_file)
        
        # Final save
        save_progress(dictionary_data, output_file)
        print(f"\nDictionary data saved to {output_file}. Total entries: {len(dictionary_data)}")
    except Exception as e:
        print(f"Unexpected error in main function: {e}")

if __name__ == "__main__":
    print("DEBUG: Script started")
    main() 