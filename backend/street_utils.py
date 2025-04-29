from typing import List, Tuple
import overpy
import shapely.geometry as sgeom

# function used to find all streets that intersect the user's created boundary.
def streets_intersecting_polygon(coords: List[Tuple[float, float]]) -> List[str]:
    # Build Shapely polygon
    poly = sgeom.Polygon([(lon, lat) for (lat, lon) in coords])
    if not poly.is_valid:
        poly = poly.buffer(0)

    # Overpass query string - find all roads touching the polygon
    polygon_str = " ".join(f"{lat} {lon}" for (lat, lon) in coords)
    query = f"""
    way(poly:"{polygon_str}") ["highway"];
    (._;>;);
    out body;
    """

    api = overpy.Overpass()
    try:
        result = api.query(query)
    except Exception as e:
        print(f"Error fetching graph: {e}")
        return []

    # Build list of street LineStrings
    highwayExclude = ['footway', 'bridleway', 'steps', 'corridor', 'path', 'via_ferrata']
    edges = []
    for way in result.ways:
        if ('highway' in way.tags and way.tags['highway'] not in highwayExclude):
            nodes = way.get_nodes(resolve_missing=True)
            points = [(float(node.lon), float(node.lat)) for node in nodes]
            if len(points) >= 2:
                edges.append(sgeom.LineString(points))

    if not edges:
        return []
    
    # find all intersections
    intersections = []
    for edge in edges:
        if edge.intersects(poly):
            intersection = edge.intersection(poly.boundary)
            if intersection.is_empty:
                continue
            if intersection.geom_type == "Point":
                intersections.append(intersection)
            elif intersection.geom_type == "MultiPoint":
                intersections.extend(intersection.geoms)
            elif intersection.geom_type == "LineString":
                intersections.append(sgeom.Point(intersection.coords[0]))
                intersections.append(sgeom.Point(intersection.coords[-1]))
            elif intersection.geom_type == "MultiLineString":
                for g in intersection.geoms:
                    intersections.append(sgeom.Point(g.coords[0]))
                    intersections.append(sgeom.Point(g.coords[-1]))

    return [(pt.y, pt.x) for pt in intersections]