import ast
import sys
from shapely.geometry import Polygon
from shapely import wkt

def polygon_to_prompt(polygon, connecting_nodes):
    boundaryCoords = list(polygon.exterior.coords)

    # find our relative coordinate zero point to base our calculations off
    minx, miny, maxx, maxy = polygon.bounds
    minBounds = (minx, miny)
    maxBounds = (maxx, maxy)
    #print("Boundary is from " + str(minBounds) + " to " + str(maxBounds))

    # set the boundary's coordinates to relative coordinates
    for i in range(len(boundaryCoords)):
        #boundaryCoords[i] = tuple(f"{x - y:.5f}" for x, y in zip(boundaryCoords[i], relativeCoordinateZero))
        boundaryCoords[i] =(round((boundaryCoords[i][0] - minx) / (maxx - minx), 5), round((boundaryCoords[i][1] - miny) / (maxy - miny), 5))
    
    # set the boundary nodes coordinates to relative ones
    for i in range(len(connecting_nodes)):
        #connecting_nodes[i] = tuple(f"{x - y:.5f}" for x, y in zip(connecting_nodes[i], relativeCoordinateZero))
        connecting_nodes[i] = (round((connecting_nodes[i][0] - minx) / (maxx - minx), 5), round((connecting_nodes[i][1] - miny) / (maxy - miny), 5))

    # form a prompt accepted by the LLM
    return "bounds: [" + str(boundaryCoords) + "]   connecting points: " + str(connecting_nodes), polygon.bounds



# - Uncomment below for command-line usage -
#polygon = Polygon(wkt.loads(sys.argv[1]))
#boundary_nodes = ast.literal_eval(sys.argv[2])
#polygon_to_prompt(polygon, boundary_nodes)