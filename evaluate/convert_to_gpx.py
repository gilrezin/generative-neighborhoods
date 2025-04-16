import ast

def convert_to_gpx(coordinate_offset, input):
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
            output += "      <trkpt lat=\"" + str((float(coordinate[0]) + coordinate_offset[0])) + "\" lon=\"" + str((float(coordinate[1]) + coordinate_offset[1])) + "\"/>\n"
        output += "    </trkseg>\n  </trk>\n"

    output += "</gpx>"
    
    with open("output.gpx", "w") as file:
        file.write(output)
    print("success!")
        
llm_output = "[[('0.00287', '0.00015'), ('0.00239', '0.00116'), ('0.00222', '0.00108'), ('0.00146', '0.00154'), ('0.00077', '0.00224'), ('0.00025', '0.00293'), ('0.00000', '0.00254'), ('0.00106', '0.00087'), ('0.00128', '0.00057'), ('0.00254', '0.00000'), ('0.00287', '0.00015')]]"
convert_to_gpx((46.72531, -117.17137), llm_output)