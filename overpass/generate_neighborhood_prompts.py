import argparse
import xml.etree.ElementTree as ET
import os
import json
import random
import copy
from collections import defaultdict
from shapely.affinity import rotate, scale
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

def get_relations(osm_root, relation):
    "Computes the convex hull polygon of a relation's member nodes"
    nodes = []
    # Get all mem. nodes that have a lat/lon attrib.
    for member in relation.findall("member"):
        if member.attrib.get("type") == "node":
            # Reference a node by its ref ID
            node = osm_root.find(f".//node[@id='{member.attrib['ref']}']")
            # Only include nots with valid lat/lon attrib.
            if node is not None and 'lat' in node.attrib and 'lon' in node.attrib:
                lon = float(node.attrib['lon'])
                lat = float(node.attrib['lat'])
                nodes.append(Point(lon, lat))
    # Merge all the points and return the convex hull
    convex_hull_nodes = unary_union(nodes)
    return convex_hull_nodes.convex_hull

def augment_convex_hull_polygon(poly, num_var = 5, max_rot_deg = 15, max_scale_per = 0.1):
    "Generate rotated and scaled variants of a convex hull polygon"
    variations = []
    for _ in range(num_var):
        # Rotate by a rand. angle between the bounds
        angle = random.uniform(-max_rot_deg, max_rot_deg)
        point1 = rotate(poly, angle, origin = 'centroid')
        # Scale by rand. factor between the bounds
        scale_factor = random.uniform(-max_scale_per, max_scale_per)
        point2 = scale(point1, xfact = scale_factor, yfact = scale_factor, origin='centroid')
        # Collect variants
        variations.append(point2)
    
    return variations

def get_bounding_box(relation_elements):
    """Extract the bounding box coordinates from relation members"""
    # In OSM, a relation's bounding box is derived from its member nodes
    # This is a simplified approach - in reality we'd need to process the actual node coordinates
    min_lat, max_lat = float('inf'), float('-inf')
    min_lon, max_lon = float('inf'), float('-inf')
    
    for member in relation_elements:
        # In a real implementation, we'd need to find the actual node coordinates
        # This is placeholder logic
        if 'lat' in member.attrib and 'lon' in member.attrib:
            lat = float(member.attrib['lat'])
            lon = float(member.attrib['lon'])
            
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
    
    if min_lat == float('inf'):
        # If no coordinates were found, return a placeholder
        return {"min_lat": None, "min_lon": None, "max_lat": None, "max_lon": None}
    
    return {
        "min_lat": min_lat,
        "min_lon": min_lon,
        "max_lat": max_lat,
        "max_lon": max_lon
    }

def get_amenities(osm_root, bbox):
    """Find all amenities within the given bounding box"""
    amenities = defaultdict(int)
    
    # Find nodes with amenity tags within the bounding box
    for node in osm_root.findall(".//node"):
        # Skip nodes outside the bounding box
        if bbox["min_lat"] is None:
            continue
            
        lat = float(node.get("lat", 0))
        lon = float(node.get("lon", 0))
        
        if (bbox["min_lat"] <= lat <= bbox["max_lat"] and 
            bbox["min_lon"] <= lon <= bbox["max_lon"]):
            
            # Check if this node has an amenity tag
            for tag in node.findall("tag"):
                if tag.get("k") == "amenity":
                    amenity_type = tag.get("v")
                    amenities[amenity_type] += 1
    
    return dict(amenities)

def get_connecting_streets(osm_root, bbox):
    """Find streets that connect to the neighborhood (crossing the boundary)"""
    connecting_streets = []
    
    # Find ways (streets) that have at least one node inside and one outside the bounding box
    for way in osm_root.findall(".//way"):
        # Check if this way is a road
        is_road = False
        road_name = None
        
        for tag in way.findall("tag"):
            if tag.get("k") == "highway":
                is_road = True
            if tag.get("k") == "name":
                road_name = tag.get("v")
        
        if not is_road or not road_name:
            continue
            
        # If we can't determine the bounding box, skip
        if bbox["min_lat"] is None:
            continue
            
        # Check if this road crosses the boundary
        nodes_inside = 0
        nodes_outside = 0
        
        for nd_ref in way.findall("nd"):
            node_id = nd_ref.get("ref")
            node = osm_root.find(f".//node[@id='{node_id}']")
            
            if node is not None:
                lat = float(node.get("lat", 0))
                lon = float(node.get("lon", 0))
                
                if (bbox["min_lat"] <= lat <= bbox["max_lat"] and 
                    bbox["min_lon"] <= lon <= bbox["max_lon"]):
                    nodes_inside += 1
                else:
                    nodes_outside += 1
        
        # If the road has nodes both inside and outside, it's a connecting road
        if nodes_inside > 0 and nodes_outside > 0:
            connecting_streets.append(road_name)
    
    return connecting_streets

def generate_prompt(neighborhood_name, bbox, amenities, connecting_streets):
    """Create a structured prompt for the neighborhood"""
    prompt = f"Generate a neighborhood similar to {neighborhood_name} with the following characteristics:\n\n"
    
    # Add bounding box
    prompt += "Bounding Box:\n"
    prompt += f"  - Latitude: {bbox['min_lat']} to {bbox['max_lat']}\n"
    prompt += f"  - Longitude: {bbox['min_lon']} to {bbox['max_lon']}\n\n"
    
    # Add amenities
    prompt += "Amenities:\n"
    for amenity_type, count in amenities.items():
        prompt += f"  - {count} {amenity_type}{'s' if count > 1 else ''}\n"
    
    if not amenities:
        prompt += "  - No specific amenities found\n"
    
    prompt += "\n"
    
    # Add connecting streets
    prompt += "Connecting Streets:\n"
    for street in connecting_streets:
        prompt += f"  - {street}\n"
    
    if not connecting_streets:
        prompt += "  - No specific connecting streets found\n"
    
    return prompt

def process_neighborhood(relation_id, osm_files):
    """Process a single neighborhood to generate its prompt"""
    neighborhood_data = {
        "id": relation_id,
        "name": None,
        "bbox": {"min_lat": None, "min_lon": None, "max_lat": None, "max_lon": None},
        "amenities": {},
        "connecting_streets": []
    }
    
    # Find the relation in the OSM files
    for file_path in osm_files:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Look for the relation with the given ID
            relation = root.find(f".//relation[@id='{relation_id}']")
            
            if relation is not None:
                # Extract neighborhood name
                for tag in relation.findall("tag"):
                    if tag.get("k") == "name":
                        neighborhood_data["name"] = tag.get("v")
                
                break
        except Exception as e:
            print(f"Error processing {file_path} for relation {relation_id}: {e}")
    
    # Generate multiple prompts
    if neighborhood_data["name"]:
        base_polygons = get_relations(root, relation)
        all_polygons = [base_polygons] + augment_convex_hull_polygon(base_polygons, num_var = 5)
        
        outputs = []
        for idx, poly in enumerate(all_polygons):
            minx, miny, maxx, maxy = poly.bounds
            bbox = {"min_lat": miny, "min_lon": minx, "max_lat": maxy, "max_lon": maxx}
            # Extract amenities
            amenities = get_amenities(root, bbox)
            # Extract connecting streets
            connecting_streets = get_connecting_streets(root, bbox)
            
            prompt = generate_prompt(
                neighborhood_data["name"],
                bbox,
                amenities,
                connecting_streets
            )
            outputs.append((f"{neighborhood_data['name'].replace(' ', '_').lower()}_{idx}", prompt))
        
        return outputs
    
    return []

def main():
    parser = argparse.ArgumentParser(description="Generate prompts for neighborhood generation")
    parser.add_argument("relation_ids_file", help="File containing neighborhood relation IDs")
    parser.add_argument("osm_dir", help="Directory containing OSM data files")
    parser.add_argument("-o", "--output_dir", default="neighborhood_prompts", help="Directory to save generated prompts")
    parser.add_argument("-n", "--num_variations", type=int, default=5, help="Number of augmentations per neighborhood")
    
    args = parser.parse_args()
    
    # Make sure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Read relation IDs
    with open(args.relation_ids_file, "r") as f:
        relation_ids = [line.strip() for line in f if line.strip()]
    
    # Get list of OSM files
    osm_files = [os.path.join(args.osm_dir, f) for f in os.listdir(args.osm_dir) 
                if f.endswith(".osm") or f.endswith(".xml")]
    
    # Process each neighborhood
    prompts_data = {}
    for relation_id in relation_ids:
        print(f"Processing neighborhood with relation ID: {relation_id}")
        variants = process_neighborhood(relation_id, osm_files, num_variations = args.num_variations)
        for suffix, prompt in variants:
            prompt_file = os.path.join(args.output_dir, f"{suffix}.txt")
            with open(prompt_file, "w") as fp:
                fp.write(prompt)
            
            prompts_data.setdefault(relation_id, []).append({"suffix": suffix, "prompt": prompt})
            print(f"  - Generated prompt: {prompt_file}")
    
    # Save all prompts to a combined JSON file
    combined_file = os.path.join(args.output_dir, "all_neighborhood_prompts.json")
    with open(combined_file, "w") as f:
        json.dump(prompts_data, f, indent=2)
    
    print(f"\nFinished generating prompts for {len(prompts_data)} neighborhoods")
    print(f"Prompts saved to directory: {args.output_dir}")

if __name__ == "__main__":
    main()
