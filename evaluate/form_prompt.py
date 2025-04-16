from shapely.geometry import Polygon

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

#Polygon([(-117.1712302377766 46.72818251656378,-117.17021260962512 46.72770295327874,-117.17030067368086 46.727538626440065,-117.16984078419759 46.72677064317452,-117.1691362722788 46.72608313808237,-117.16844643828229 46.725570018818786,-117.16883294114024 46.72531513412477,-117.17050615637211 46.72637826321031,-117.17080948747551 46.72659625246513,-117.17137701074608 46.72785721882141,-117.1712302377766 46.72818251656378)])
polygon = Polygon([
    (46.72818251656378, -117.1712302377766),
    (46.72770295327874, -117.17021260962512),
    (46.727538626440065, -117.17030067368086),
    (46.72677064317452, -117.16984078419759),
    (46.72608313808237, -117.1691362722788),
    (46.725570018818786, -117.16844643828229),
    (46.72531513412477, -117.16883294114024),
    (46.72637826321031, -117.17050615637211),
    (46.72659625246513, -117.17080948747551),
    (46.72785721882141, -117.17137701074608),
    (46.72818251656378, -117.1712302377766)
])
boundary_nodes = [(46.72541765447292, -117.16864702193722)]
polygon_to_prompt(polygon, boundary_nodes)