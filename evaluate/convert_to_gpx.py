import ast
import sys

# Converts relative coordinates to .gpx files for viewing. 
def convert_to_gpx(minBounds, maxBounds, input):
    lines = ast.literal_eval(input)

    output = ""

    output += """
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1" 
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 
                         http://www.topografix.com/GPX/1/1/gpx.xsd">
"""

    for line in lines:
        output += "  <trk>\n    <trkseg>\n"
        for coordinate in line:
            # convert back to geographic coordinates
            output += "      <trkpt lat=\"" + str(round(float((coordinate[0])) * (maxBounds[0] - minBounds[0]) + minBounds[0], 5)) + "\" lon=\"" + str(round(float(coordinate[1]) * (maxBounds[1] - minBounds[1]) + minBounds[1], 5)) + "\"/>\n"
        output += "    </trkseg>\n  </trk>\n"

    output += "</gpx>"
    
    # write to .gpx file
    with open("output.gpx", "w") as file:
        file.write(output)
    print("success!")

# - Uncomment below for command-line usage -
#convert_to_gpx(ast.literal_eval(sys.argv[1]), ast.literal_eval(sys.argv[2]), sys.argv[3])
