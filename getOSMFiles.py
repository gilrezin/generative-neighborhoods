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

# get our data from the API
api = overpy.Overpass()

# 1384962, 7820445
# relations will come from our neighborhoods list
# [1198693, 1198698, 1446499, 1446509, 1455020, 1457988, 1703041, 2253101, 2253102, 2963686, 4040742, 4266659, 4446297, 4446316, 4446351, 4446395, 4734450, 5850457, 6247824, 7057368, 7057369, 7057788, 7206679, 7340078, 7350028, 7354373, 7354383, 7360323, 7426476, 7878934, 8250238, 8339894, 8589627, 8589634, 8589639, 8589640, 9086645, 9103568, 9151269, 9161661, 9161691, 9161853, 9187207, 9306376, 9350834, 9365250, 9370356, 9373580, 9373581, 9387023, 9394371, 9397393, 9435565, 9451056, 9453997, 9469807, 9470047, 9470055, 9470086, 9470122, 9486530, 9488302, 9492118, 9509654, 9509670, 9515252, 9515253, 9534158, 9677451, 9680775, 9906535, 9906544, 9941157, 9961757, 10358441, 10358604, 10386834, 10530886, 10731846, 10813501, 10813502, 10813503, 10813504, 10813505, 10815480, 10876776, 10932689, 11308186, 11308187, 11309275, 11309276, 11313011, 11313013, 11319165, 11319171, 11931751, 11938169, 11952476, 11952477, 12015792, 12247421, 12249419, 12249464, 12341923, 12341926, 12341928, 12341935, 12341937, 12341938, 12341943, 12341945, 12341948, 12341956, 12341958, 12341959, 12341961, 12341963, 12341973, 12341975, 12341976, 12341986, 12341990, 12341991, 12341994, 12342007, 12378257, 12378324, 12378913, 12503000, 12743735, 12743736, 12744691, 12744692, 12748128, 12772314, 12795425, 12832666, 12912908, 13102771, 13117004, 13126600, 13266098, 13266100, 13266101, 13532522, 13532532, 13634704, 13640149, 13657692, 13662963, 13673645, 13674762, 13674763, 13712046, 13712049, 13716109, 13716110, 13725607, 13729264, 13729660, 13732458, 13749307, 13749335, 13753005, 13753007, 13759827, 13760679, 13778971, 13782791, 13782880, 13783014, 13783633, 13792777, 13792806, 13793133, 13793689, 13793738, 13808133, 13815559, 13816064, 13818054, 13819070, 13823696, 13823754, 13823831, 13824049, 13836234, 13857597, 13933836, 13934567, 13934775, 13936725, 13951391, 13956473, 13959042, 14036734, 14089980, 14089981, 14110335, 14205248, 14205600, 14205610, 14221291, 14239345, 14239351, 14239354, 14239365, 14248789, 14248794, 14248871, 14248875, 14251725, 14280345, 14280346, 14280348, 14280349, 14280357, 14301192, 14301219, 14314067, 14326511, 14326536, 14326544, 14326597, 14329324, 14329617, 14341632, 14341842, 14341845, 14389641, 14439946, 14439947, 14439952, 14439954, 14439955, 14439956, 14439957, 14450762, 14450845, 14459934, 14462799, 14462870, 14497649, 14548448, 14548587, 14548700, 14548708, 14565792, 14565794, 14565800, 14568825, 14606803, 14606804, 14607183, 14628319, 14631514, 14631515, 14631646, 14631649, 14688431, 14759660, 14759662, 14759663, 14769235, 14769242, 14862267, 14940134, 14940137, 14940138, 14940139, 14940141, 14940143, 14940151, 14943219, 14943220, 14943223, 14958682, 14966597, 15093574, 15335699, 15335702, 15390189, 15394147, 15396655, 15405419, 15419621, 15428007, 15434105, 15434106, 15446345, 15446346, 15446348, 15446349, 15446427, 15446428, 15446429, 15446430, 15457255, 15457256, 15457257, 15457258, 15461100, 15461119, 15461245, 15537187, 15549995, 15744020, 15744022, 15744024, 15748141, 15748143, 15750453, 15762573, 15776025, 15802935, 15840852, 15867501, 15867506, 15906968, 15906969, 15913847, 15925758, 15950593, 15955956, 15956293, 15959932, 15959973, 15965332, 15967573, 16058719, 16111577, 16121780, 16121782, 16146201, 16146330, 16146331, 16149228, 16149540, 16149545, 16156293, 16156294, 16180162, 16341892, 16399126, 16457829, 16457830, 16478615, 16497261, 16522897, 16567408, 16567409, 16568027, 16568028, 16603703, 16603709, 16603722, 16606269, 16606286, 16606287, 16606765, 16606801, 16606808, 16606810, 16606815, 16606831, 16606870, 16637244, 16731716, 16750819, 16758369, 16952620, 17006360, 17007996, 17052932, 17052939, 17053121, 17053848, 17053898, 17053902, 17053958, 17057221, 17058083, 17150811, 17152790, 17208253, 17240984, 17240985, 17332645, 17335038, 17335039, 17339069, 17347616, 17350394, 17364553, 17364554, 17371171, 17424961, 17425315, 17425324, 17429403, 17434731, 17445055, 17445073, 17445074, 17459945, 17473955, 17475469, 17475470, 17475471, 17493964, 17493965, 17493966, 17493967, 17493968, 17493969, 17495565, 17503378, 17504152, 17529321, 17539506, 17571168, 17571169, 17571170, 17575510, 17577930, 17586469, 17586471, 17586477, 17590975, 17626200, 17717590, 17717664, 17718227, 17723419, 17723420, 17723421, 17723422, 17723423, 17723424, 17723425, 17723426, 17723427, 17723429, 17723433, 17723458, 17748095, 17763129, 17845751, 17850652, 17850752, 17850753, 17850754, 17850755, 17850758, 17850760, 17913695, 17914152, 17914153, 17916406, 17916407, 17936984, 17997371, 18099548, 18099550, 18099553, 18310041, 18339316, 18339763, 18354098, 18360362, 18378686, 18639050, 18643152, 18681687, 18799838, 18800512, 18800881, 18800882, 18878837, 18906642, 18906700, 18910975, 18917285, 18917286, 18917318, 18917322, 18986740, 18986932]
relations = [1384962, 7820445]
highwayExclude = ['footway', 'bridleway', 'steps', 'corridor', 'path', 'via_ferrata']

nodesQueue = Queue()
boundaryNodesQueue = Queue()

# ensures that the way is valid, then inserts it into the list
def validate_and_insert_nodes(way, polygon):

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
        print("empty line")
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
            else:
                for coordinates in boundaryIntersection.coords:
                    boundaryNodesQueue.put((coordinates[0], coordinates[1]))

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
    #print("Our relative coordinate zeroing point is " + str(relativeCoordinateZero))

    # set the boundary's coordinates to relative coordinates
    for i in range(len(boundaryCoords)):
        boundaryCoords[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryCoords[i], relativeCoordinateZero))
    
    # set the boundary nodes coordinates to relative ones
    for i in range(len(boundaryNodes)):
        boundaryNodes[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryNodes[i], relativeCoordinateZero))

    # set the nodes of the road's coordinates to relative ones
    for i in range(len(nodesList)):
        for j in range(len(nodesList[i])):
            nodesList[i][j] = tuple(f"{x - y:.5f}" for x, y in zip(nodesList[i][j], relativeCoordinateZero))

    return nodesList, boundaryNodesList, boundaryCoords
        


# for every relation, get our neighborhood data

with open("training_data.txt", "w") as file:
    file.write("training_data = [\n")

    for relation in relations:
        print(relation)
        nodesList, boundaryNodesList, boundary = get_relation_data(relation)

        # convert all the absolute geographic coordinates to relative ones
        relativeNodesList, relativeBoundaryNodesList, relativeBoundaryList = convert_absolute_to_relative_coords(nodesList, boundaryNodesList, boundary)

        new_entry = {'text_input': 'bounds: ' + str(relativeNodesList) + '   connecting points: ' + str(relativeBoundaryNodesList), 'output': str(nodesList)}
        file.write("  " + str(new_entry) + "\n")
        file.flush()

    file.write("]")