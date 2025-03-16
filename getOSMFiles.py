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
from queue import Queue

# get our data from the API
api = overpy.Overpass()

# relations will come from our neighborhoods list
relations = [7820445, 1384962]

nodes = Queue()
boundaryNodes = Queue()

# ensures that the way is valid, then inserts it into the list
def validate_and_insert_nodes(way, polygon):
    
    # exclude all non-roads from our dataset
    if not 'highway' in way.tags:
        return

    nodes = way.get_nodes(resolve_missing=True)

    # linestring wants longitude before latitude. Not really sure why
    line = LineString([(node.lat, node.lon) for node in nodes])

    # find the intersection of the lines
    intersection = polygon.intersection(line)
    boundaryIntersection = (polygon.boundary).intersection(line)
    
    if intersection.is_empty: 
        # no relation to polygon
        print("empty line")
        return

    elif isinstance(intersection, LineString):
        # Single intersection (either partially or entirely within polygon)
        contained_nodes = list(intersection.coords)
        nodes.put(contained_nodes)
        nodes.task_done()

        # if partially within the polygon, find the boundary intersection point and add it to the boundaryNodes list
        if not boundaryIntersection.is_empty:
            if (type(boundaryIntersection) is shapely.geometry.multipoint.MultiPoint):
                intersectionPoint = boundaryIntersection.geoms[0]
            else:
                intersectionPoint = boundaryIntersection.coords[0]
            boundaryNodes.put(intersectionPoint)
            boundaryNodes.task_done()

    elif isinstance(intersection, MultiLineString):
        # Multiple intersections
        segment_count = 0
        for segment in intersection.geoms:
            contained_nodes = list(segment.coords)
            nodes.put(contained_nodes)
            nodes.task_done()

            # if partially within the polygon, find the boundary intersection point and add it to the boundaryNodes list
            if not boundaryIntersection.is_empty:
                intersectionPoint = boundaryIntersection.coords[0]
                boundaryNodes.put(tuple(intersectionPoint))
                boundaryNodes.task_done()
            segment_count += 1

# 
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
    # print(shapely.validation.explain_validity(polygons[0]))
    # index = next((i for i, way in enumerate(result.ways) if way.id == 97734347), -1)
    # nodes = result.ways[index].get_nodes(resolve_missing=True)
    # line = LineString([(node.lat, node.lon) for node in nodes])
    
    # x, y = polygons[0].exterior.xy  # Extract exterior coordinates
    # # Plot the polygon
    # plt.plot(y, x)
    # plt.xlabel("Longitude")
    # plt.ylabel("Latitude")
    # plt.title("Polygon of Geographic Coordinates")

    # x2,y2 = line.xy
    # plt.plot(y2,x2)
    # plt.show()
    # - END DEBUGGING -

    bound_validate_and_insert_nodes = partial(validate_and_insert_nodes, polygon=polygons[0])

    # multithread the node add process (speeds up by many factors)
    with ThreadPoolExecutor() as executor:
        executor.map(bound_validate_and_insert_nodes, result.ways)

    # way_count = 0
    # for way in result.ways:
    #     validate_and_insert_nodes(way, polygons[0]) 
    #     print(way_count)
    #     way_count += 1

    # move from queue to list
    boundaryNodesList = []
    while not boundaryNodes.empty():
        boundaryNodesList.append(boundaryNodes.get())

    nodesList = []
    while not nodes.empty():
        nodesList.append(nodes.get())

    # - DEBUGGING - display all boundary nodes over the neighborhood
    # for point in boundaryNodesList:
    #     plt.plot(y, x)
    #     plt.plot(point[1], point[0], marker='o', color='orange')
    # plt.show()
    # print()
    # - END DEBUGGING -

# for every relation, get our neighborhood data
for relation in relations:
    print(relation)
    get_relation_data(relation)

# test for a single relation
#get_relation_data(1384962)