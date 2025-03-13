# generative-neighborhoods
Uses a fine-tuned LLM to create new urban neighborhoods.

## Usage
**extract_relation_ids.py**

Parses each .osm (or .xml) file, collects all relation IDs, remove duplicates, then writes to neighborhood_ids.txt.

1. Place all Overpass XML output files into directory 'overpass_output_data'
2. Run 'extract_relation_ids.py' by:
```
python3 extract_relation_ids.py overpass_output_data/*.osm -o neighborhood_ids.txt
```