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
import copy
import random
from getrelations import filter_relations

# get our data from the API
api = overpy.Overpass()

# test relations: 1384962, 7820445
relations = filter_relations()
highwayExclude = ['footway', 'bridleway', 'steps', 'corridor', 'path', 'via_ferrata']

nodesQueue = Queue()
boundaryNodesQueue = Queue()

invalid_polygon = False

# ensures that the way is valid, then inserts it into the list
def validate_and_insert_nodes(way, polygon):
    global invalid_polygon
    if (not invalid_polygon):
        # exclude all non-roads and pedestrian paths from our dataset
        if not 'highway' in way.tags or way.tags['highway'] in highwayExclude:
            return

        nodes = way.get_nodes(resolve_missing=True)

        line = LineString([(node.lat, node.lon) for node in nodes])

        # find the intersection of the lines
        intersection = polygon.intersection(line)
        boundaryIntersection = (polygon.boundary).intersection(line)
        
        if intersection.is_empty: 
            # no relation to polygon
            #global invalid_polygon
            invalid_polygon = True
            print("invalid, skipping this polygon")
            return

        elif isinstance(intersection, LineString):
            # Single intersection (either partially or entirely within polygon)
            contained_nodes = list(intersection.coords)
            nodesQueue.put(contained_nodes)

            # if partially within the polygon, find the boundary intersection point and add it to the boundaryNodes list
            if not boundaryIntersection.is_empty:
                if (type(boundaryIntersection) is shapely.geometry.multipoint.MultiPoint):
                    intersectionPoint = boundaryIntersection.geoms[0]
                else:
                    intersectionPoint = boundaryIntersection.coords[0]
                boundaryNodesQueue.put(intersectionPoint)

        elif isinstance(intersection, MultiLineString):
            # Multiple intersections
            for segment in intersection.geoms:
                contained_nodes = list(segment.coords)
                nodesQueue.put(contained_nodes)

            # if partially within the polygon, find the boundary intersection point and add it to the boundaryNodes list
            if not boundaryIntersection.is_empty:
                if (type(boundaryIntersection) is shapely.geometry.multipoint.MultiPoint):
                    for coordinates in boundaryIntersection.geoms:
                        boundaryNodesQueue.put((coordinates.x, coordinates.y))
                elif (type(boundaryIntersection) is shapely.geometry.LineString):
                    for coordinates in boundaryIntersection.coords:
                        boundaryNodesQueue.put((coordinates[0], coordinates[1]))
                else:
                    print("not implemented, skipping this polygon")
                    invalid_polygon = True
    else:
        return

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
    # nodesDebug = result.ways[index].get_nodes(resolve_missing=True)
    # line = LineString([(node.lat, node.lon) for node in nodesDebug])
    
    # x, y = polygons[0].exterior.xy  # Extract exterior coordinates
    # # Plot the polygon
    # plt.plot(y, x)
    # plt.xlabel("Longitude")
    # plt.ylabel("Latitude")
    # plt.title("Polygon of Geographic Coordinates")
    # # - END DEBUGGING -

    global invalid_polygon
    invalid_polygon = False
    for way in result.ways:
        validate_and_insert_nodes(way, polygons[0])
    #print(nodesQueue.qsize())
    #print(boundaryNodesQueue.qsize())

    # move from queue to list
    boundaryNodesList = []
    while not boundaryNodesQueue.empty():
        value = boundaryNodesQueue.get()
        if isinstance(value, tuple):
            boundaryNodesList.append(value)

    nodesList = []
    while not nodesQueue.empty():
        nodesList.append(nodesQueue.get())

    # - DEBUGGING - display all boundary nodes over the neighborhood
    # for point in boundaryNodesList:
    #     plt.plot(y, x)
    #     plt.plot(point[1], point[0], marker='o', color='orange')
    # plt.show()
    # - END DEBUGGING -

    return nodesList, boundaryNodesList, polygons[0]

def convert_absolute_to_relative_coords(nodesList, boundaryNodes, boundary):
    boundaryCoords = list(boundary.exterior.coords)

    # find our relative coordinate zero point to base our calculations off
    minx, miny, maxx, maxy = boundary.bounds
    relativeCoordinateZero = (minx, miny)
    relativeCoordinateMin = (minx, miny)
    relativeCoordinateMax = (maxx, maxy)
    #print("Our relative coordinate zeroing point is " + str(relativeCoordinateZero))

    # set the boundary's coordinates to relative coordinates
    for i in range(len(boundaryCoords)):
        # for each tuple, subtract by the zeroing coordinate
        boundaryCoords[i] =(round((boundaryCoords[i][0] - minx) / (maxx - minx), 5), round((boundaryCoords[i][1] - miny) / (maxy - miny), 5))
        #boundaryCoords[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryCoords[i], relativeCoordinateZero))
    
    # set the boundary nodes coordinates to relative ones
    for i in range(len(boundaryNodes)):
        #boundaryNodes[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryNodes[i], relativeCoordinateZero))
        boundaryNodes[i] = (round((boundaryNodes[i][0] - minx) / (maxx - minx), 5), round((boundaryNodes[i][1] - miny) / (maxy - miny), 5))

    # set the nodes of the road's coordinates to relative ones
    for i in range(len(nodesList)):
        for j in range(len(nodesList[i])):
            #nodesList[i][j] = tuple(f"{x - y:.5f}" for x, y in zip(nodesList[i][j], relativeCoordinateZero))
            nodesList[i][j] = (round((nodesList[i][j][0] - minx) / (maxx - minx), 5), round((nodesList[i][j][1] - miny) / (maxy - miny), 5))

    return nodesList, boundaryNodesList, boundaryCoords
        

# for every relation, get our neighborhood data

with open("training_data.txt", "w") as file:

    for relation in relations:
        # skip any relations that have already been completed (default: 0)
        if (relation >= 0):
            print(relation)
            #nodesList, boundaryNodesList, boundary = get_relation_data(relations[relations.index(8589640)])
            #match random.randint(0,5):
                    
            nodesList, boundaryNodesList, boundary = get_relation_data(relation)

            if (not invalid_polygon):
                # convert all the absolute geographic coordinates to relative ones
                relativeNodesList, relativeBoundaryNodesList, relativeBoundaryList = convert_absolute_to_relative_coords(nodesList, boundaryNodesList, boundary)

                # uncomment for ChatGPT formatted dataset
                #new_entry = '''{\"messages\": [{\"role\": \"system\", \"content\": \"Your job is to draw new neighborhoods given the coordinate boundaries listed by the user. Within those boundaries, draw roads from the supplied connecting points with the format [[(lat, long), (lat, long)]] where the inner square brackets represent a single road and every coordinate pair represents a point on that road.\"}, {\"role\": \"user\", \"content\": \"bounds: ''' + str(relativeNodesList) + '   connecting points: ' + str(relativeBoundaryNodesList) + '''\"}, {\"role\": \"assistant\", \"content\": \"''' + str(nodesList) + "\"}]}"

                # uncomment for Gemini formatted dataset
                new_entry = "  [\"bounds: " + str(relativeBoundaryList) + '   connecting points: ' + str(relativeBoundaryNodesList) + '\", \"' + str(relativeNodesList) + '\"],'

                file.write(new_entry + "\n")
                file.flush()