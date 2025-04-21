from typing import List, Tuple
import osmnx as ox
import shapely.geometry as sgeom
import geopandas as gpd
from shapely.strtree import STRtree

ox.settings.log_console = False
ox.settings.use_cache = True

def streets_intersecting_polygon(coords: List[Tuple[float, float]]) -> List[str]:
    poly = sgeom.Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)

    # Set EPSG:4326, then reproject to UTM manually (Zone 11 for Pullman WA)
    gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326").to_crs("EPSG:32611")

    # Buffer in meters (110m), then return to EPSG:4326
    buffered = gdf.buffer(110).to_crs("EPSG:4326").iloc[0]

    # Now use OSMnx without any CRS guessing
    graph = ox.graph_from_polygon(buffered, retain_all=True)
    edges = ox.utils_graph.graph_to_gdfs(graph, nodes=False)[["geometry", "name"]]

    # Do intersection
    strtree = STRtree(edges.geometry.values)
    idxs = strtree.query(poly)

    streets = set()
    for i in idxs:
        geom = edges.geometry.values[i]
        if geom.intersects(poly):
            name = edges.iloc[i]["name"]
            if isinstance(name, list):
                streets.update(filter(None, name))
            elif name:
                streets.add(name)

    return sorted(streets)
