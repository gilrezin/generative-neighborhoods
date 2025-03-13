import glob
import argparse
import xml.etree.ElementTree as ET

def extract_relation_ids_from_xml(filename):
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Unable to parse {filename}: {e}")
        return []

    relation_ids = []
    # Each <relation> element should have an 'id' attribute
    for relation in root.findall("relation"):
        rel_id = relation.get("id")
        if rel_id is not None:
            relation_ids.append(rel_id)
    return relation_ids

def main():
    parser = argparse.ArgumentParser(
        description="Extract <relation> IDs from Overpass XML files."
    )
    # Handles paths to one or more Overpass XML files
    parser.add_argument(
        "files",
        nargs="+",
    )
    # Output file to store all unique relation IDs
    parser.add_argument(
        "-o", "--output",
        default="relation_ids.txt",
    )

    args = parser.parse_args()

    all_ids = set()
    for filename in args.files:
        rel_ids = extract_relation_ids_from_xml(filename)
        all_ids.update(rel_ids)

    # Sort numerically before writing
    sorted_ids = sorted(all_ids, key=lambda x: int(x))

    with open(args.output, "w", encoding="utf-8") as f:
        for rel in sorted_ids:
            f.write(rel + "\n")

    print(f"Extracted {len(sorted_ids)} unique relation IDs to file {args.output}")

if __name__ == "__main__":
    main()