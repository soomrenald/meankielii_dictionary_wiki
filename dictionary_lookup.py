import xml.etree.ElementTree as ET
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path
import shutil
from datetime import datetime
import os

# Set up logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Translation:
    word: str
    pos: str  # part of speech
    examples: List[str] = None
    notes: str = None

class Dictionary:
    def __init__(self, xml_path: str, lookup_js_path: str):
        """Initialize the dictionary with the XML file and lookup.js metadata."""
        self.xml_path = xml_path
        self.lookup_js_path = lookup_js_path
        self.tree = None
        self.root = None
        self.metadata = {}
        self.load_dictionary()
        self.load_metadata()

    def create_backup(self):
        """Create a backup of the current dictionary state."""
        backup_dir = Path("backup")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"dictionary_backup_{timestamp}.xml"
        
        shutil.copy2(self.xml_path, backup_path)
        logger.info(f"Created backup at {backup_path}")

    def add_entry(self, meankieli: str, swedish: str, pos: str, user: str) -> bool:
        """
        Add a new entry to the dictionary.
        Returns True if successful, False otherwise.
        """
        try:
            # Create backup before modifying
            self.create_backup()
            
            # Create new word element
            word_elem = ET.Element("w")
            word_elem.set("v", meankieli.lower())
            
            # Create left element (Meänkieli)
            l_elem = ET.SubElement(word_elem, "l")
            l_elem.text = meankieli
            
            # Add part of speech
            s_elem = ET.SubElement(l_elem, "s")
            s_elem.set("n", pos)
            
            # Add user note
            note_elem = ET.SubElement(l_elem, "s")
            note_elem.set("n", f"note:Added by {user}")
            
            # Create right element (Swedish)
            r_elem = ET.SubElement(word_elem, "r")
            s_elem = ET.SubElement(r_elem, "s")
            s_elem.set("n", f"t:{swedish}")
            
            # Add to root
            self.root.append(word_elem)
            
            # Save changes
            self.tree.write(self.xml_path, encoding='utf-8', xml_declaration=True)
            
            # Reload dictionary to update in-memory state
            self.load_dictionary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding entry: {str(e)}")
            return False

    def load_dictionary(self):
        """Load and parse the XML dictionary file."""
        try:
            logger.info(f"Loading dictionary from {self.xml_path}")
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
            logger.info("Dictionary loaded successfully")
        except ET.ParseError as e:
            logger.error(f"Error parsing XML file: {str(e)}")
            raise

    def load_metadata(self):
        """Load and parse the lookup.js file to extract metadata for XML tags."""
        try:
            with open(self.lookup_js_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract metadata from lookup.js (assuming it's in a specific format)
                # This is a placeholder; adjust the parsing logic based on the actual structure of lookup.js
                self.metadata = {"s": "noun", "a": "adjective", "adv": "adverb", "v": "verb", "en": "name", "pos": "postposition", "pron": "pronoun", "num": "numeral", "konj": "conjunction", "ij": "interjection", "prep": "preposition"}
                logger.info("Metadata loaded successfully")
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            raise

    def get_pos_tag(self, node) -> str:
        """Extract part of speech tag from a node."""
        for s_node in node.findall("s"):
            n_attr = s_node.get("n", "")
            if n_attr in ['s', 'a', 'adv', 'v', 'en', 'pos', 'pron', 'num', 'konj', 'ij', 'prep']:
                return self.metadata.get(n_attr, n_attr)
        return ""

    def get_examples(self, r_elem) -> Tuple[List[str], List[str]]:
        """Extract example sentences in both Meänkieli (exS) and Swedish (exT) from the <r> tag."""
        meankieli_examples = []
        swedish_examples = []
        for s_elem in r_elem.findall("s"):
            n_attr = s_elem.get("n", "")
            if n_attr.startswith("exS:"):
                meankieli_examples.append(n_attr[4:].strip())  # Remove 'exS:' prefix
            elif n_attr.startswith("exT:"):
                swedish_examples.append(n_attr[4:].strip())  # Remove 'exT:' prefix
        return meankieli_examples, swedish_examples

    def get_notes(self, node) -> str:
        """Extract any notes or additional information from a node."""
        notes = []
        for s_node in node.findall("s"):
            n_attr = s_node.get("n", "")
            if n_attr.startswith("note"):
                notes.append(s_node.text.strip() if s_node.text else "")
        return " ".join(notes) if notes else None

    def search_word(self, word: str, direction: str = "meänkieli-sv") -> List[Dict]:
        """
        Search for a word in the dictionary.
        direction: "meänkieli-sv" for Meänkieli to Swedish, "sv-meänkieli" for Swedish to Meänkieli
        """
        word = word.lower()
        results = []

        # Find all word entries
        for word_elem in self.root.findall(".//w"):
            source = word_elem.get("v", "").lower()
            if source == word:  # Changed from startswith to exact match
                logger.info(f"Found matching word: {source}")
                # Get all translations
                for l_elem in word_elem.findall("l"):
                    meankieli = l_elem.text.strip() if l_elem.text else ""
                    pos = self.get_pos_tag(l_elem)
                    notes = self.get_notes(l_elem)

                    # Get all right elements (translations)
                    for r_elem in word_elem.findall("r"):
                        swedish = ""
                        for s_elem in r_elem.findall("s"):
                            n_attr = s_elem.get("n", "")
                            logger.info(f"Found attribute: {n_attr}")  # Debug output
                            if n_attr.startswith("t:"):  # Changed from t= to t:
                                swedish = n_attr[2:].strip()  # Extract the Swedish word
                                logger.info(f"Found Swedish translation: {swedish}")  # Debug output
                                break
                        
                        if meankieli and swedish:  # Ensure both Meänkieli and Swedish are present
                            meankieli_examples, swedish_examples = self.get_examples(r_elem)
                            if direction == "meänkieli-sv":
                                results.append({
                                    'source': meankieli,
                                    'target': swedish,
                                    'pos': pos,
                                    'meankieli_examples': meankieli_examples,
                                    'swedish_examples': swedish_examples,
                                    'notes': notes
                                })
                            else:  # sv-meänkieli
                                results.append({
                                    'source': swedish,
                                    'target': meankieli,
                                    'pos': pos,
                                    'meankieli_examples': meankieli_examples,
                                    'swedish_examples': swedish_examples,
                                    'notes': notes
                                })

        logger.info(f"Found {len(results)} results for word: {word}")
        return results

    def search_word_exact(self, word: str, direction: str = "meänkieli-sv") -> List[Dict]:
        """
        Search for exact word matches in the dictionary.
        direction: "meänkieli-sv" for Meänkieli to Swedish, "sv-meänkieli" for Swedish to Meänkieli
        """
        word = word.lower()
        search_words = word.split()  # Split search phrase into words
        results = []

        # Find all word entries
        for word_elem in self.root.findall(".//w"):
            source = word_elem.get("v", "").lower()
            
            # Get all translations
            for l_elem in word_elem.findall("l"):
                meankieli = l_elem.text.strip() if l_elem.text else ""
                pos = self.get_pos_tag(l_elem)
                notes = self.get_notes(l_elem)

                # Get all right elements (translations)
                for r_elem in word_elem.findall("r"):
                    swedish = ""
                    for s_elem in r_elem.findall("s"):
                        n_attr = s_elem.get("n", "")
                        if n_attr.startswith("t:"):
                            swedish = n_attr[2:].strip()
                            break
                    
                    if meankieli and swedish:
                        # Split translations by various separators and clean each part
                        separators = [',', '.', '/', ';', '|', '•', '·']
                        target_parts = [swedish]
                        for sep in separators:
                            new_parts = []
                            for part in target_parts:
                                new_parts.extend(part.split(sep))
                            target_parts = [p.strip().lower() for p in new_parts if p.strip()]
                        
                        # For exact matches, check if all search words appear in the translation
                        if direction == "sv-meänkieli":
                            # Check if any of the target parts exactly matches the search phrase
                            if word in target_parts:
                                meankieli_examples, swedish_examples = self.get_examples(r_elem)
                                results.append({
                                    'source': swedish,
                                    'target': meankieli,
                                    'pos': pos,
                                    'meankieli_examples': meankieli_examples,
                                    'swedish_examples': swedish_examples,
                                    'notes': notes
                                })
                        elif source == word:  # Exact match in source language
                            meankieli_examples, swedish_examples = self.get_examples(r_elem)
                            results.append({
                                'source': meankieli,
                                'target': swedish,
                                'pos': pos,
                                'meankieli_examples': meankieli_examples,
                                'swedish_examples': swedish_examples,
                                'notes': notes
                            })

        logger.info(f"Found {len(results)} exact matches for word: {word}")
        return results

    def search_word_partial(self, word: str, direction: str = "meänkieli-sv") -> List[Dict]:
        """
        Search for words that contain the search term as a substring.
        direction: "meänkieli-sv" for Meänkieli to Swedish, "sv-meänkieli" for Swedish to Meänkieli
        """
        word = word.lower()
        search_words = word.split()  # Split search phrase into words
        results = []

        # Find all word entries
        for word_elem in self.root.findall(".//w"):
            source = word_elem.get("v", "").lower()
            
            # Get all translations
            for l_elem in word_elem.findall("l"):
                meankieli = l_elem.text.strip() if l_elem.text else ""
                pos = self.get_pos_tag(l_elem)
                notes = self.get_notes(l_elem)

                # Get all right elements (translations)
                for r_elem in word_elem.findall("r"):
                    swedish = ""
                    for s_elem in r_elem.findall("s"):
                        n_attr = s_elem.get("n", "")
                        if n_attr.startswith("t:"):
                            swedish = n_attr[2:].strip()
                            break
                    
                    if meankieli and swedish:
                        if direction == "sv-meänkieli":
                            # For Swedish to Meänkieli, check if all search words appear in the translation
                            translation_text = swedish.lower()
                            if all(search_word in translation_text for search_word in search_words):
                                meankieli_examples, swedish_examples = self.get_examples(r_elem)
                                results.append({
                                    'source': swedish,
                                    'target': meankieli,
                                    'pos': pos,
                                    'meankieli_examples': meankieli_examples,
                                    'swedish_examples': swedish_examples,
                                    'notes': notes
                                })
                        elif word in source:  # Partial match in source language
                            meankieli_examples, swedish_examples = self.get_examples(r_elem)
                            results.append({
                                'source': meankieli,
                                'target': swedish,
                                'pos': pos,
                                'meankieli_examples': meankieli_examples,
                                'swedish_examples': swedish_examples,
                                'notes': notes
                            })

        logger.info(f"Found {len(results)} partial matches for word: {word}")
        return results

    def search_word_in_examples(self, word: str, direction: str = "meänkieli-sv") -> List[Dict]:
        """
        Search for the word in example sentences.
        direction: "meänkieli-sv" for Meänkieli to Swedish, "sv-meänkieli" for Swedish to Meänkieli
        """
        word = word.lower()
        results = []

        # Find all word entries
        for word_elem in self.root.findall(".//w"):
            source = word_elem.get("v", "").lower()
            # Get all translations
            for l_elem in word_elem.findall("l"):
                meankieli = l_elem.text.strip() if l_elem.text else ""
                pos = self.get_pos_tag(l_elem)
                notes = self.get_notes(l_elem)

                # Get all right elements (translations)
                for r_elem in word_elem.findall("r"):
                    swedish = ""
                    for s_elem in r_elem.findall("s"):
                        n_attr = s_elem.get("n", "")
                        if n_attr.startswith("t:"):
                            swedish = n_attr[2:].strip()
                            break
                    
                    if meankieli and swedish:
                        meankieli_examples, swedish_examples = self.get_examples(r_elem)
                        # Check if word appears in examples
                        found_in_examples = False
                        if direction == "meänkieli-sv":
                            for ex in meankieli_examples:
                                if word in ex.lower():
                                    found_in_examples = True
                                    break
                        else:  # sv-meänkieli
                            for ex in swedish_examples:
                                if word in ex.lower():
                                    found_in_examples = True
                                    break

                        if found_in_examples:
                            if direction == "meänkieli-sv":
                                results.append({
                                    'source': meankieli,
                                    'target': swedish,
                                    'pos': pos,
                                    'meankieli_examples': meankieli_examples,
                                    'swedish_examples': swedish_examples,
                                    'notes': notes
                                })
                            else:  # sv-meänkieli
                                results.append({
                                    'source': swedish,
                                    'target': meankieli,
                                    'pos': pos,
                                    'meankieli_examples': meankieli_examples,
                                    'swedish_examples': swedish_examples,
                                    'notes': notes
                                })

        logger.info(f"Found {len(results)} matches in examples for word: {word}")
        return results

    def save_results(self, results: List[Dict], base_filename: str):
        """Save results in both JSON and CSV formats."""
        # Save as JSON
        json_filename = f"{base_filename}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Results saved to {json_filename}")

        # Save as CSV
        csv_filename = f"{base_filename}.csv"
        df = pd.DataFrame(results)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        logger.info(f"Results saved to {csv_filename}")

def print_results(results: List[Dict], search_type: str):
    """Print the search results in a formatted way."""
    if results:
        print(f"\n{search_type} Results:")
        for entry in results:
            print(f"\n{entry['source']} ({entry['pos']}): {entry['target']}")
            if entry['meankieli_examples'] or entry['swedish_examples']:
                print("  Examples:")
                for me, se in zip(entry['meankieli_examples'], entry['swedish_examples']):
                    print(f"    Meänkieli: {me}")
                    print(f"    Swedish: {se}")
            if entry['notes']:
                print(f"  Notes: {entry['notes']}")
    else:
        print(f"\n{search_type}: No results found.")

def main():
    # Initialize dictionary
    dict_path = "fit-swe-lr-trie.xml"
    lookup_js_path = "lookup.js"
    dictionary = Dictionary(dict_path, lookup_js_path)

    # Test word
    test_word = "kirja"
    
    # Test all three search methods
    print(f"\nSearching for '{test_word}' using different methods:")
    
    # 1. Exact match
    print("\n=== Exact Match Search ===")
    results = dictionary.search_word_exact(test_word, "meänkieli-sv")
    print_results(results, "Meänkieli → Swedish")
    results = dictionary.search_word_exact(test_word, "sv-meänkieli")
    print_results(results, "Swedish → Meänkieli")
    
    # 2. Partial match
    print("\n=== Partial Match Search ===")
    results = dictionary.search_word_partial(test_word, "meänkieli-sv")
    print_results(results, "Meänkieli → Swedish")
    results = dictionary.search_word_partial(test_word, "sv-meänkieli")
    print_results(results, "Swedish → Meänkieli")
    
    # 3. Example text search
    print("\n=== Example Text Search ===")
    results = dictionary.search_word_in_examples(test_word, "meänkieli-sv")
    print_results(results, "Meänkieli → Swedish")
    results = dictionary.search_word_in_examples(test_word, "sv-meänkieli")
    print_results(results, "Swedish → Meänkieli")

if __name__ == "__main__":
    main() 