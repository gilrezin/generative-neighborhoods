# import overpass
import overpy
from shapely.geometry import Polygon, Point, LineString, MultiLineString
from shapely.affinity import rotate
from shapely.affinity import scale
from shapely.ops import polygonize
import shapely.validation
from queue import Queue
import random
from dataset.get_relations import filter_relations
import numpy as np

# get our data from the API
api = overpy.Overpass()

# test relations: 1384962, 7820445
relations = filter_relations()
highwayExclude = ['footway', 'bridleway', 'steps', 'corridor', 'path', 'via_ferrata']

nodesQueue = Queue()
boundaryNodesQueue = Queue()

invalid_polygon = False

# function that ensures that the way is valid, then inserts it into the list
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

# function that gets the associated relation data from a relation id
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


# function to augment a geographic value in the dataset with reflections across the x/y axis.
def convert_absolute_to_relative_coords(nodesList, boundaryNodes, boundary):
    boundaryCoords = list(boundary.exterior.coords)

    # find our relative coordinate zero point to base our calculations off
    minx, miny, maxx, maxy = boundary.bounds

    # set the boundary's coordinates to relative coordinates
    for i in range(len(boundaryCoords)):
        # for each tuple, subtract by the zeroing coordinate
        boundaryCoords[i] =((boundaryCoords[i][0] - minx) / (maxx - minx), (boundaryCoords[i][1] - miny) / (maxy - miny))
        #boundaryCoords[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryCoords[i], relativeCoordinateZero))
    
    # set the boundary nodes coordinates to relative ones
    for i in range(len(boundaryNodes)):
        #boundaryNodes[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryNodes[i], relativeCoordinateZero))
        boundaryNodes[i] = ((boundaryNodes[i][0] - minx) / (maxx - minx), (boundaryNodes[i][1] - miny) / (maxy - miny))

    # set the nodes of the road's coordinates to relative ones
    for i in range(len(nodesList)):
        for j in range(len(nodesList[i])):
            #nodesList[i][j] = tuple(f"{x - y:.5f}" for x, y in zip(nodesList[i][j], relativeCoordinateZero))
            nodesList[i][j] = ((nodesList[i][j][0] - minx) / (maxx - minx), (nodesList[i][j][1] - miny) / (maxy - miny))

    return nodesList, boundaryNodesList, boundaryCoords


# function to augment a geographic value in the dataset with minor jitters to the coordinates.
def jitter_points(nodesList, boundaryNodesList, boundary):
    for i in range(len(nodesList)):
        for j in range(len(nodesList[i])):
            nodesList[i][j] = (nodesList[i][j][0] + random.uniform(-0.0001, 0.0001), nodesList[i][j][1] + random.uniform(-0.0001, 0.0001))

    return nodesList, boundaryNodesList, boundary


# function to augment a geographic value in the dataset with variations in rotation.
def rotate_relation_data(nodesList, boundaryNodesList, boundary):
    angle_degrees = random.randint(-12, 12) * 15
    angle_rad = np.deg2rad(angle_degrees)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)

    rotation_matrix = np.array([
        [cos_a, -sin_a],
        [sin_a,  cos_a]
    ])

    # Rotation process: convert to np array, shift to origin (centered), rotate, then shift back, output as list

    # rotate nodesList
    rotatedNodesList = []
    for group in nodesList:
        list_np = np.array(group)
        shifted = list_np - (0.5, 0.5)
        rotated = shifted @ rotation_matrix.T
        result = rotated + (0.5, 0.5)
        rotatedNodesList.append([tuple(float(x) for x in pt) for pt in result])
    
    # rotate boundaryNodesList
    list_np = np.array(boundaryNodesList)
    shifted = list_np - (0.5, 0.5)
    rotated = shifted @ rotation_matrix.T
    rotatedBoundaryNodesList = rotated + (0.5, 0.5)

    # rotate boundary
    list_np = np.array(boundary)
    shifted = list_np - (0.5, 0.5)
    rotated = shifted @ rotation_matrix.T
    rotatedBoundary = rotated + (0.5, 0.5)

    return rotatedNodesList, rotatedBoundaryNodesList.tolist(), rotatedBoundary.tolist()


# function to augment a geographic value in the dataset with reflections across the x/y axis.
def reflect_relation_data(relativeNodesList, relativeBoundaryNodesList, relativeBoundary):
    reflect_x = 1
    reflect_y = 0
    if (random.random() > 0.5):
        reflect_x = 0
        reflect_y = 1

    for i in range(len(relativeNodesList)):
        for j in range(len(relativeNodesList[i])):
            relativeNodesList[i][j] = (abs(reflect_x - relativeNodesList[i][j][0]), abs(reflect_y - relativeNodesList[i][j][1]))

    for i in range(len(relativeBoundaryNodesList)):
        relativeBoundaryNodesList[i] = (abs(reflect_x - relativeBoundaryNodesList[i][0]), abs(reflect_y - relativeBoundaryNodesList[i][1]))

    for i in range(len(relativeBoundary)):
        relativeBoundary[i] = (abs(reflect_x - relativeBoundary[i][0]), abs(reflect_y - relativeBoundary[i][1]))

    return relativeNodesList, relativeBoundaryNodesList, relativeBoundary

def round_relation_data(augmentedNodesList, augmentedBoundaryNodesList, augmentedBoundary):
    round_decimal = 5

    for i in range(len(augmentedBoundary)):
        augmentedBoundary[i] = (round(augmentedBoundary[i][0], round_decimal), round(augmentedBoundary[i][1], round_decimal))

    for i in range(len(augmentedBoundaryNodesList)):
        augmentedBoundaryNodesList[i] = (round(augmentedBoundaryNodesList[i][0], round_decimal), round(augmentedBoundaryNodesList[i][1], round_decimal))

    for i in range(len(augmentedNodesList)):
        for j in range(len(augmentedNodesList[i])):
            augmentedNodesList[i][j] = (round(augmentedNodesList[i][j][0], round_decimal), round(augmentedNodesList[i][j][1], round_decimal))

    return augmentedNodesList, augmentedBoundaryNodesList, augmentedBoundary


# for every relation, get our neighborhood data
with open("training_data.txt", "w") as file:

    for relation in relations:
        # skip any relations that have already been completed (default: 0)
        if (relation >= 0):
            print(relation)

            nodesList, boundaryNodesList, boundary = get_relation_data(relation)

            # start the process if the polygon isn't broken
            if (not invalid_polygon and len(boundaryNodesList) > 0):
                    # convert all the absolute geographic coordinates to relative ones
                    relativeNodesList, relativeBoundaryNodesList, relativeBoundaryList = convert_absolute_to_relative_coords(nodesList, boundaryNodesList, boundary)

                    roundedNodesList, roundedBoundaryNodesList, roundedBoundary = round_relation_data(nodesList, boundaryNodesList, boundary)
                    new_entry = '''{\"contents\": [{\"role\": \"user\", \"parts\": [{\"text\": \"bounds: ''' + str(roundedBoundary) + '   connecting points: ' + str(roundedBoundaryNodesList) + '''\"}]}, {\"role\": \"model\", \"parts\": [{\"text\": \"''' + str(roundedNodesList) + '''\"}]}]}'''

                    file.write(new_entry + "\n")
                    file.flush()

                    # repeat multiple times to get many augmentations for the data
                    for i in range(random.randint(3,5)):
                        match (random.randint(0,2)):
                            case 0: # rotate
                                print("rotate")
                                augmentedNodesList, augmentedBoundaryNodesList, augmentedBoundary = rotate_relation_data(relativeNodesList, relativeBoundaryNodesList, relativeBoundaryList)
                            case 1: # reflect
                                print("reflect")
                                augmentedNodesList, augmentedBoundaryNodesList, augmentedBoundary = reflect_relation_data(relativeNodesList, relativeBoundaryNodesList, relativeBoundaryList)
                            case 2: # jitter
                                print("jitter")
                                augmentedNodesList, augmentedBoundaryNodesList, augmentedBoundary = jitter_points(relativeNodesList, relativeBoundaryNodesList, relativeBoundaryList)

                        # round every value to 5 decimal points
                        roundedNodesList, roundedBoundaryNodesList, roundedBoundary = round_relation_data(augmentedNodesList, augmentedBoundaryNodesList, augmentedBoundary)

                        # Gemini 2.0 fine-tuning formatt
                        new_entry = '''{\"contents\": [{\"role\": \"user\", \"parts\": [{\"text\": \"bounds: ''' + str(roundedBoundary) + '   connecting points: ' + str(roundedBoundaryNodesList) + '''\"}]}, {\"role\": \"model\", \"parts\": [{\"text\": \"''' + str(roundedNodesList) + '''\"}]}]}'''

                        file.write(new_entry + "\n")
                        file.flush()