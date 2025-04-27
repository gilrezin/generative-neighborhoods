from typing import List, Tuple
import osmnx as ox
import shapely.geometry as sgeom
import geopandas as gpd
from shapely.strtree import STRtree

ox.settings.log_console = False
ox.settings.use_cache = True

# def streets_intersecting_polygon(coords: List[Tuple[float, float]]) -> List[str]:
#     poly = sgeom.Polygon(coords)
#     if not poly.is_valid:
#         poly = poly.buffer(0)

#     # Set EPSG:4326, then reproject to UTM manually (Zone 11 for Pullman WA)
#     gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")
#     utm_crs = "EPSG:32611"  # UTM Zone 11N for Pullman, WA
    
#     # Buffer in meters (110m) in UTM CRS for accurate distance
#     buffered = gdf.to_crs(utm_crs).buffer(110).to_crs("EPSG:4326")
#     buffered_crs_iloc = buffered.iloc[0]

#     # Create graph using the polygon in WGS84 but specify network_type if needed
#     graph = ox.graph_from_polygon(
#         buffered_crs_iloc,
#         retain_all=True,
#         network_type='all',  # or 'drive', 'walk', 'bike' as needed
#         crs="EPSG:4326"  # explicitly tell OSMnx the input CRS
#     )
    
#     edges = ox.utils_graph.graph_to_gdfs(graph, nodes=False)[["geometry", "name"]]


#     # Do intersection
#     strtree = STRtree(edges.geometry.values)
#     idxs = strtree.query(poly)

#     streets = set()
#     for i in idxs:
#         geom = edges.geometry.values[i]
#         if geom.intersects(poly):
#             name = edges.iloc[i]["name"]
#             if isinstance(name, list):
#                 streets.update(filter(None, name))
#             elif name:
#                 streets.add(name)

#     return sorted(streets)

def streets_intersecting_polygon(coords: List[Tuple[float, float]]) -> List[str]:

    poly = sgeom.Polygon([(lon, lat) for (lat, lon) in coords])
    if not poly.is_valid:
        poly = poly.buffer(0)

    # Simple small buffer in degrees (~0.001 degree ~ 111 meters at equator)
    # Adjust slightly depending on latitude if desired, but for now keep simple
    buffer_distance = 0.001  # roughly 110m in degrees
    buffered_poly = poly.buffer(buffer_distance)

    # Get street network inside buffered polygon
    graph = ox.graph_from_polygon(
        buffered_poly,
        retain_all=True,
        network_type='all'
    )

    # Extract edges as GeoDataFrame
    edges = ox.utils_graph.graph_to_gdfs(graph, nodes=False)[["geometry", "name"]]

    # Build spatial index
    strtree = STRtree(edges.geometry.values)
    idxs = strtree.query(poly)

    intersections = []
    for i in idxs:
        geom = edges.geometry.values[i]
        if geom.intersects(poly):
            intersection = geom.intersection(poly.boundary)  # <-- note: polygon *boundary* here
            if intersection.is_empty:
                continue
            if intersection.geom_type == "Point":
                intersections.append(intersection)
            elif intersection.geom_type == "MultiPoint":
                intersections.extend(intersection.geoms)
            elif intersection.geom_type == "LineString":
                # Sometimes a street edge just touches the boundary along a segment
                # Grab the ends of the segment
                intersections.append(sgeom.Point(intersection.coords[0]))
                intersections.append(sgeom.Point(intersection.coords[-1]))
            elif intersection.geom_type == "MultiLineString":
                for g in intersection.geoms:
                    intersections.append(sgeom.Point(g.coords[0]))
                    intersections.append(sgeom.Point(g.coords[-1]))

    # streets = set()
    # for i in idxs:
    #     print(i)
    #     geom = edges.geometry.values[i]
    #     if geom.intersects(poly):
    #         name = edges.iloc[i]["name"]
    #         if isinstance(name, list):
    #             streets.update(filter(None, name))
    #         elif name:
    #             streets.add(name)

    return [(pt.y, pt.x) for pt in intersections]