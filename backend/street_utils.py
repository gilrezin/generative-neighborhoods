"""
street_utils.py  –  thin wrappers around osmnx/shapely for clarity
"""
from typing import List, Tuple
import osmnx as ox
import shapely.geometry as sgeom
from shapely.strtree import STRtree

# Suppress OSMnx’s logging noise
ox.settings.log_console = False
ox.settings.use_cache = True

def streets_intersecting_polygon(coords: List[Tuple[float, float]]) -> List[str]:
    """
    Given polygon vertices (lat, lon) in the same order Leaflet spits out,
    return a **unique** list of street names whose geometries intersect it.
    """
    poly = sgeom.Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)  # quick fix for self‑intersections

    # Pull only the road network inside a small bounding box to avoid over‑fetch
    graph = ox.graph_from_polygon(poly.buffer(0.001))   # ~110 m buffer
    gdf   = ox.utils_graph.graph_to_gdfs(graph, nodes=False)[['geometry', 'name']]

    # Fast spatial index
    strtree = STRtree(gdf.geometry.values)
    idxs    = strtree.query(poly)

    streets = set()
    for i in idxs:
        geom = gdf.geometry.values[i]
        if geom.intersects(poly):
            name = gdf.iloc[i]['name']
            # gdf['name'] can be None or a list; normalise to string(s)
            if isinstance(name, list):
                streets.update(filter(None, name))
            elif name:
                streets.add(name)

    return sorted(streets)
