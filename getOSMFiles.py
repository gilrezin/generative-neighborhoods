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

def validate_and_insert_nodes(way, polygon, minx, miny, maxx, maxy):
    
    nodes = way.get_nodes(resolve_missing=True)

    # linestring wants longitude before latitude. Not really sure why
    line = LineString([(node.lon, node.lat) for node in nodes])

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

    # #for node in nodes:
    # #newNode = Point(node.lat, node.lon)
    # # check if in proximity to the bbox (speeds up the search process)
    # #if minx <= newNode.x <= maxx and miny <= newNode.y <= maxy:
    # # check if the node is beyond the specified bbox
    # if (polygon.contains(line)):
    #     nodesList.append(newNode)

    # # check if the node is a boundary node (ex: street connecting to the neighborhood)
    # elif (polygon.intersects(newNode)):
    #     boundaryNodes.append(newNode)

    # if neither, discard this node

def get_relation_data(relation):
    # TODO: the area and rel numbers should come from list relations. Area = rel + 3600000000
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
    bbox = []
    # the items we need to access from our object are:
    # result.relations[0].members[i].geometry[j].lat
    # result.relations[0].members[i].geometry[j].lon
    for member in result.relations[0].members:
        if type(member) == overpy.RelationWay:
            coords = [(geometry.lon, geometry.lat) for geometry in member.geometry]
            #for geometry in member.geometry:
                

                #lat = geometry.lat
                #lon = geometry.lon
                # add the points to our bounding box
                #bbox.append((lat, lon))
            newLineString = LineString(coords)
            bbox.append(newLineString)

    # form a polygon from our bounding box
    polygons = list(polygonize(bbox))
    polygon = polygons[0]
    #polygon = Polygon(bbox)
    #polygon = orient(polygon)
    print(shapely.validation.explain_validity(polygon))
    minx, miny, maxx, maxy = polygon.bounds

    nodes = result.ways[166].get_nodes(resolve_missing=True)
    line = LineString([(node.lon, node.lat) for node in nodes])
    
    x, y = polygon.exterior.xy  # Extract exterior coordinates
    # Plot the polygon
    plt.plot(x, y)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Polygon of Geographic Coordinates")

    x2,y2 = line.xy
    plt.plot(x2,y2)
    plt.show()

    bound_validate_and_insert_nodes = partial(validate_and_insert_nodes, polygon=polygon, minx=minx, miny=miny, maxx=maxx, maxy=maxy)

    # multithread the node add process (speeds up by many factors)
    # with ThreadPoolExecutor() as executor:
    #     executor.map(bound_validate_and_insert_nodes, result.ways)
    
    validate_and_insert_nodes(result.ways[132], polygon, minx, miny, maxx, maxy)
            


    print(nodesList)
    print(boundaryNodes)



# for every relation, get our neighborhood data
# for relation in relations:
#     get_relation_data(relation)
get_relation_data(3431135)


# TODO: save the output to a JSON file