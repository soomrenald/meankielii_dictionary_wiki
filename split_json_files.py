import json
import os
import shutil
from datetime import datetime

def split_json_file(input_file, max_size_mb=90):
    # Create backup directory if it doesn't exist
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Create backup of original file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"{os.path.basename(input_file)}.backup_{timestamp}")
    shutil.copy2(input_file, backup_file)
    print(f"[INFO] Created backup: {backup_file}")
    
    # Read the original JSON file
    print(f"[INFO] Loading JSON data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"[INFO] Loaded JSON file with {len(data)} top-level entries.")
    
    # Flatten the nested array structure
    print(f"[INFO] Flattening nested array structure...")
    flattened_data = []
    for idx, subarray in enumerate(data):
        if isinstance(subarray, list):
            flattened_data.extend(subarray)
        else:
            flattened_data.append(subarray)
        if idx % 100 == 0:
            print(f"[DEBUG] Flattened {idx+1} top-level entries...")
    print(f"[INFO] Total flattened entries: {len(flattened_data)}")
    
    # Calculate chunk size (90MB to be safe)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # Split into chunks
    print(f"[INFO] Splitting data into chunks of ~{max_size_mb}MB...")
    chunks = []
    current_chunk = []
    current_size = 0
    
    for i, entry in enumerate(flattened_data, 1):
        entry_str = json.dumps(entry, ensure_ascii=False)
        entry_size = len(entry_str.encode('utf-8'))
        
        if current_size + entry_size > max_size_bytes:
            chunks.append(current_chunk)
            print(f"[DEBUG] Created chunk {len(chunks)} with {len(current_chunk)} entries.")
            current_chunk = [entry]
            current_size = entry_size
        else:
            current_chunk.append(entry)
            current_size += entry_size
        if i % 1000 == 0:
            print(f"[DEBUG] Processed {i} entries...")
    
    if current_chunk:
        chunks.append(current_chunk)
        print(f"[DEBUG] Created chunk {len(chunks)} with {len(current_chunk)} entries.")
    
    # Save chunks
    base_name = os.path.splitext(input_file)[0]
    for i, chunk in enumerate(chunks, 1):
        output_file = f"{base_name}_part{i}.json"
        print(f"[INFO] Saving chunk {i} to {output_file} ({len(chunk)} entries)...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Created chunk {i}: {output_file} ({len(chunk)} entries)")
    
    return len(chunks)

def main():
    # Find all large JSON files
    json_files = [f for f in os.listdir('.') if f.endswith('.json') and os.path.getsize(f) > 100 * 1024 * 1024]
    
    if not json_files:
        print("No large JSON files found.")
        return
    
    print(f"Found {len(json_files)} large JSON files to split:")
    for i, file in enumerate(json_files, 1):
        size_mb = os.path.getsize(file) / (1024 * 1024)
        print(f"{i}. {file} ({size_mb:.2f} MB)")
    
    for file in json_files:
        print(f"\nProcessing {file}...")
        num_chunks = split_json_file(file)
        print(f"Split {file} into {num_chunks} chunks")

if __name__ == "__main__":
    main() 