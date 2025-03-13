# import overpass
import overpy
from shapely.geometry import Polygon, Point

# get our data from the API
api = overpy.Overpass()

# TODO: the area and rel numbers should come from list relations. Area = rel + 3600000000
result = api.query("""
area(3607820455)->.searchArea;
(
  way(area.searchArea);
  rel(7820455);
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
        for geometry in member.geometry:
            lat = geometry.lat
            lon = geometry.lon

            # add the points to our bounding box
            bbox.append((lat, lon))

# form a polygon from our bounding box
polygon = Polygon(bbox)


# TODO: from our list of neighborhood relation ids
#relations = [3607820445, 3607820446]

# TODO: for every relation, get our neighborhood data
#for relation in relations:


# TODO: identify every node that is beyond the specified bbox and remove

# TODO: save the output to a JSON file