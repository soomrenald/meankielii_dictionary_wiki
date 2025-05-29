import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from dictionary_lookup import Dictionary
import logging

# Set up logging to only show errors and warnings
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AddEntryDialog:
    def __init__(self, parent, dictionary):
        self.top = tk.Toplevel(parent)
        self.top.title("Add New Entry")
        self.top.geometry("400x300")
        self.dictionary = dictionary
        
        # Create and pack widgets
        ttk.Label(self.top, text="Meänkieli:").pack(pady=5)
        self.meankieli_var = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.meankieli_var).pack(pady=5)
        
        ttk.Label(self.top, text="Swedish:").pack(pady=5)
        self.swedish_var = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.swedish_var).pack(pady=5)
        
        ttk.Label(self.top, text="Part of Speech:").pack(pady=5)
        self.pos_var = tk.StringVar()
        pos_combo = ttk.Combobox(self.top, textvariable=self.pos_var)
        pos_combo['values'] = (
            'noun',
            'adjective',
            'adverb',
            'verb',
            'name',
            'postposition',
            'pronoun',
            'numeral',
            'conjunction',
            'interjection',
            'preposition'
        )
        pos_combo.pack(pady=5)
        
        ttk.Label(self.top, text="User:").pack(pady=5)
        self.user_var = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.user_var).pack(pady=5)
        
        ttk.Button(self.top, text="Add Entry", command=self.add_entry).pack(pady=20)
        
        # Make dialog modal
        self.top.transient(parent)
        self.top.grab_set()
        
    def add_entry(self):
        meankieli = self.meankieli_var.get().strip()
        swedish = self.swedish_var.get().strip()
        pos = self.pos_var.get().strip()
        user = self.user_var.get().strip()
        
        if not all([meankieli, swedish, pos, user]):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        # Convert full part of speech label to short code
        pos_codes = {
            'noun': 's',
            'adjective': 'a',
            'adverb': 'adv',
            'verb': 'v',
            'name': 'en',
            'postposition': 'pos',
            'pronoun': 'pron',
            'numeral': 'num',
            'conjunction': 'konj',
            'interjection': 'ij',
            'preposition': 'prep'
        }
        pos_code = pos_codes.get(pos, pos)
        
        if self.dictionary.add_entry(meankieli, swedish, pos_code, user):
            messagebox.showinfo("Success", "Entry added successfully!")
            self.top.destroy()
        else:
            messagebox.showerror("Error", "Failed to add entry!")

class DictionaryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Meänkieli Dictionary")
        self.root.geometry("1200x800")
        
        # Initialize dictionary
        self.dictionary = Dictionary("fit-swe-lr-trie.xml", "lookup.js")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Search frame
        self.search_frame = ttk.Frame(self.main_frame)
        self.search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Search label and entry
        ttk.Label(self.search_frame, text="Search word:").grid(row=0, column=0, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, padx=5)
        
        # Add Entry button
        self.add_button = ttk.Button(self.search_frame, text="Add Entry", command=self.show_add_dialog)
        self.add_button.grid(row=0, column=2, padx=5)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, width=100, height=40)
        self.results_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        self.search_frame.columnconfigure(1, weight=1)
        
        # Debounce variables
        self.debounce_id = None
        self.debounce_delay = 300  # milliseconds
        
        # Bind KeyRelease event to search entry for live search
        self.search_entry.bind('<KeyRelease>', self.on_key_release)
        
        # Set focus to search entry
        self.search_entry.focus()

    def show_add_dialog(self):
        """Show the dialog for adding a new entry."""
        AddEntryDialog(self.root, self.dictionary)

    def format_result(self, result):
        """Format a single result entry for display."""
        text = f"{result['source']} ({result['pos']}): {result['target']}\n"
        if result['meankieli_examples'] or result['swedish_examples']:
            text += "  Examples:\n"
            for me, se in zip(result['meankieli_examples'], result['swedish_examples']):
                text += f"    Meänkieli: {me}\n"
                text += f"    Swedish: {se}\n"
        if result['notes']:
            text += f"  Notes: {result['notes']}\n"
        text += "\n"
        return text

    def remove_duplicates(self, results):
        """Remove duplicate entries based on word pairs."""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create a tuple of the word pair in alphabetical order to ensure consistent comparison
            word_pair = tuple(sorted([result['source'].lower(), result['target'].lower()]))
            if word_pair not in seen:
                seen.add(word_pair)
                unique_results.append(result)
        
        return unique_results

    def on_key_release(self, event):
        # Debounce: cancel previous scheduled search if any
        if self.debounce_id is not None:
            self.root.after_cancel(self.debounce_id)
        self.debounce_id = self.root.after(self.debounce_delay, self.perform_search)

    def perform_search(self):
        word = self.search_var.get().strip()
        if not word:
            self.results_text.delete(1.0, tk.END)
            return
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Always search exact matches in both directions
        meankieli_to_sv_exact = self.dictionary.search_word_exact(word, "meänkieli-sv")
        sv_to_meankieli_exact = self.dictionary.search_word_exact(word, "sv-meänkieli")
        exact_results = meankieli_to_sv_exact + sv_to_meankieli_exact
        
        # If word is 4 or more characters, also search partial matches
        partial_results = []
        if len(word) >= 4:
            meankieli_to_sv_partial = self.dictionary.search_word_partial(word, "meänkieli-sv")
            sv_to_meankieli_partial = self.dictionary.search_word_partial(word, "sv-meänkieli")
            partial_results = meankieli_to_sv_partial + sv_to_meankieli_partial
            
            # Remove partial results that are already in exact results
            exact_word_pairs = {tuple(sorted([r['source'].lower(), r['target'].lower()])) for r in exact_results}
            partial_results = [r for r in partial_results 
                             if tuple(sorted([r['source'].lower(), r['target'].lower()])) not in exact_word_pairs]
        
        # Display results
        if exact_results:
            self.results_text.insert(tk.END, f"Found {len(exact_results)} exact matches:\n\n")
            for result in exact_results:
                self.results_text.insert(tk.END, self.format_result(result))
        
        if partial_results:
            if exact_results:
                self.results_text.insert(tk.END, "\n" + "="*50 + "\n\n")
            self.results_text.insert(tk.END, f"Found {len(partial_results)} partial matches:\n\n")
            for result in partial_results:
                self.results_text.insert(tk.END, self.format_result(result))
        
        if not exact_results and not partial_results:
            self.results_text.insert(tk.END, "No matches found.\n")

def main():
    root = tk.Tk()
    app = DictionaryGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 