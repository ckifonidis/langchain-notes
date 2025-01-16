import json
import os

from datetime import datetime

def create_files_from_json(json_string, directory="."):
    try:
        json_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format") from e

    files = json_data.get("files", [])
    
    if not files:
        print("No files to create.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_directory = os.path.join(directory, timestamp)
    os.makedirs(target_directory, exist_ok=True)

    for file in files:
        filename = file.get("filename")
        code = file.get("code", "")
        
        if not filename:
            print("Skipping entry: missing filename.")
            continue

        # Write the code to the file
        filepath = os.path.join(target_directory, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
            print(f"Created file: {filename}")
