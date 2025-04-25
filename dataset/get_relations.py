import overpy
import pickle
from shapely.geometry import Polygon, Point, LineString, MultiLineString
from shapely.geometry.polygon import orient
from shapely.ops import polygonize

# generates a new object containing all relations (~5min to generate)
def get_admin_relations():
    api = overpy.Overpass()
    
    # Define bounding boxes (lat1, lon1, lat2, lon2)
    bbox = [24.396308, -141.0, 63, -50]
    
    query = f"""
    (
    relation["boundary"="administrative"]["admin_level"~"10|11"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );
    out geom;
    """

    result = api.query(query)

    with open("all_relations.pkl", "wb") as f:
        pickle.dump(result, f)

def filter_relations():
    relations = []

    # open a file, where you stored the pickled data
    file = open('all_relations.pkl', 'rb')

    # dump information to that file
    data = pickle.load(file)

    for relation in range(len(data.relations)):

        bbox = []
        for member in data.relations[relation].members:
            # only RelationWay objects contain linestrings
            if type(member) == overpy.RelationWay:

                # create our polygon out of linestrings
                coords = [(geometry.lat, geometry.lon) for geometry in member.geometry]
                newLineString = LineString(coords)
                bbox.append(newLineString)
            
        # form a polygon from our bounding box
        polygons = list(polygonize(bbox))

        # only obtain small neighborhoods
        if (len(polygons) > 0 and polygons[0].area > 0 and polygons[0].area < 0.00002):
            relations.append(data.relations[relation].id)

    print(len(relations))
    return relations