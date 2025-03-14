# import overpass
import overpy
from shapely.geometry import Polygon, Point, LineString, MultiLineString
from shapely.geometry.polygon import orient
from shapely.ops import polygonize
import shapely.validation
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from itertools import groupby

# get our data from the API
api = overpy.Overpass()

relations = [7820445, 7820446]

nodesList = []
boundaryNodes = []

def validate_and_insert_nodes(way, polygon):
    
    nodes = way.get_nodes(resolve_missing=True)

    # linestring wants longitude before latitude. Not really sure why
    line = LineString([(node.lat, node.lon) for node in nodes])

    # find the intersection of the lines
    intersection = polygon.intersection(line)
    
    if intersection.is_empty: 
        # contained entirely within polygon
        nodesList.append(nodes)

    elif isinstance(intersection, LineString):
        # Single intersection
        contained_nodes = list(intersection.coords)
        nodesList.append(contained_nodes)
        boundaryNodes.append(intersection.coords[0])

    elif isinstance(intersection, MultiLineString):
        # Multiple intersections
        segment_count = 0
        for segment in intersection:
            contained_nodes = list(segment.coords)
            nodesList.append(contained_nodes)
            boundaryNodes.append(intersection.coords[segment_count])
            segment_count += 1

def get_relation_data(relation):
    # call the API with our desired area and relation
    result = api.query("""
    area(""" + str(relation + 3600000000) + """)->.searchArea;
    (
    way(area.searchArea);
    rel(""" + str(relation) + """);
    <;
    );
    out geom;
    """)


    # get our bounding box from our relation
    # the items we need to access from our object are:
    # result.relations[0].members[i].geometry[j].lat
    # result.relations[0].members[i].geometry[j].lon
    bbox = []

    for member in result.relations[0].members:

        # only RelationWay objects contain linestrings
        if type(member) == overpy.RelationWay:

            # create our polygon out of linestrings
            coords = [(geometry.lat, geometry.lon) for geometry in member.geometry]
            newLineString = LineString(coords)
            bbox.append(newLineString)

    # form a polygon from our bounding box
    polygons = list(polygonize(bbox))

    # - DEBUGGING - plot the relation and the way to check for intersection
    print(shapely.validation.explain_validity(polygons[0]))
    index = next((i for i, way in enumerate(result.ways) if way.id == 1291524296), -1)
    nodes = result.ways[index].get_nodes(resolve_missing=True)
    line = LineString([(node.lat, node.lon) for node in nodes])
    
    x, y = polygons[0].exterior.xy  # Extract exterior coordinates
    # Plot the polygon
    plt.plot(y, x)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Polygon of Geographic Coordinates")

    x2,y2 = line.xy
    plt.plot(y2,x2)
    plt.show()
    # - END DEBUGGING -

    bound_validate_and_insert_nodes = partial(validate_and_insert_nodes, polygon=polygons[0])

    # multithread the node add process (speeds up by many factors)
    with ThreadPoolExecutor() as executor:
        executor.map(bound_validate_and_insert_nodes, result.ways)
            
    print(nodesList)
    print(len(nodesList))
    print(boundaryNodes)
    print(len(boundaryNodes))

# for every relation, get our neighborhood data
# for relation in relations:
#     get_relation_data(relation)
get_relation_data(9592519)