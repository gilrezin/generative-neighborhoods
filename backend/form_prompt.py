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

#Polygon([(-117.1712302377766 46.72818251656378,-117.17021260962512 46.72770295327874,-117.17030067368086 46.727538626440065,-117.16984078419759 46.72677064317452,-117.1691362722788 46.72608313808237,-117.16844643828229 46.725570018818786,-117.16883294114024 46.72531513412477,-117.17050615637211 46.72637826321031,-117.17080948747551 46.72659625246513,-117.17137701074608 46.72785721882141,-117.1712302377766 46.72818251656378)])
#polygon = Polygon(wkt.loads(sys.argv[1]))
#polygon = Polygon(wkt.loads("POLYGON ((46.7425847 -117.1839684, 46.744797 -117.183859, 46.744545 -117.180501, 46.742673 -117.178002, 46.7425847 -117.1839684))"))
#boundary_nodes = ast.literal_eval(sys.argv[2])
#boundary_nodes = ast.literal_eval("[(46.742728, -117.183959), (46.7433419, -117.1839353), (46.7442683, -117.183887), (46.743489, -117.179094), (46.7430662, -117.1785196), (46.7426545, -117.1801298)]")
#polygon_to_prompt(polygon, boundary_nodes)