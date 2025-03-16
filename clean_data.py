import requests
import time
import xml.etree.ElementTree as ET
import os

# Overpass API URL
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Input and output directories
RELATION_IDS_FILE = "relation_ids.txt"
RAW_DATA_DIR = "raw_osm_data"
CLEANED_DATA_DIR = "cleaned_osm_data"

# Ensure directories exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(CLEANED_DATA_DIR, exist_ok=True)

# Function to fetch OSM data for a given relation ID
def fetch_osm_data(relation_id):
    query = f"""
    area({int(relation_id) + 3600000000})->.searchArea;
    (
      way(area.searchArea);
      <;
    );
    out geom;
    """
    response = requests.get(OVERPASS_URL, params={"data": query})
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch data for relation {relation_id}: {response.status_code}")
        return None

# Fetch and save OSM data
def download_osm_data():
    with open(RELATION_IDS_FILE, "r") as f:
        relation_ids = [line.strip() for line in f.readlines()]
    
    for rel_id in relation_ids:
        print(f"Fetching data for relation {rel_id}...")
        data = fetch_osm_data(rel_id)
        if data:
            filename = os.path.join(RAW_DATA_DIR, f"{rel_id}.osm")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(data)
            print(f"Saved {filename}")
        time.sleep(1)  # Avoid overloading the API

# Function to clean OSM data
def clean_osm_data():
    for file in os.listdir(RAW_DATA_DIR):
        if file.endswith(".osm"):
            filepath = os.path.join(RAW_DATA_DIR, file)
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Remove unnecessary metadata
            for meta in root.findall("meta"):
                root.remove(meta)
            for note in root.findall("note"):
                root.remove(note)
            
            # Filter relevant elements
            valid_elements = {"node", "way", "relation"}  # Keep essential data
            for elem in list(root):
                if elem.tag not in valid_elements:
                    root.remove(elem)
            
            # Save cleaned file
            cleaned_filepath = os.path.join(CLEANED_DATA_DIR, file)
            tree.write(cleaned_filepath, encoding="utf-8")
            print(f"Cleaned and saved {cleaned_filepath}")

if __name__ == "__main__":
    print("Starting OSM data download...")
    download_osm_data()
    print("Starting OSM data cleaning...")
    clean_osm_data()
    print("Dataset processing complete!")
