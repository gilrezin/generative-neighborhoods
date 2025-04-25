import ast
import sys
from shapely.geometry import Polygon
from shapely import wkt

# Converts Polygon boundary and list of connecting points along the boundary into a prompt for the LLM.
def polygon_to_prompt(polygon, connecting_nodes):
    boundaryCoords = list(polygon.exterior.coords)

    # find our relative coordinate zero point to base our calculations off
    minx, miny, maxx, maxy = polygon.bounds
    relativeCoordinateZero = (minx, miny)
    print("Our relative coordinate zeroing point is " + str(relativeCoordinateZero))

    # set the boundary's coordinates to relative coordinates
    for i in range(len(boundaryCoords)):
        boundaryCoords[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryCoords[i], relativeCoordinateZero))
    
    # set the boundary nodes coordinates to relative ones
    for i in range(len(connecting_nodes)):
        connecting_nodes[i] = tuple(f"{x - y:.5f}" for x, y in zip(connecting_nodes[i], relativeCoordinateZero))

    # form a prompt accepted by the LLM
    print("bounds: [" + str(boundaryCoords) + "]   connecting points: " + str(connecting_nodes))

# input values from the command line
polygon = Polygon(wkt.loads(sys.argv[1]))
boundary_nodes = ast.literal_eval(sys.argv[2])
polygon_to_prompt(polygon, boundary_nodes)