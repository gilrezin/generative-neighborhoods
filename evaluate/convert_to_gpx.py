import ast

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
            output += "      <trkpt lat=\"" + str(round(float(coordinate[0]) * (maxBounds[0] - minBounds[0]) + minBounds[0], 5)) + "\" lon=\"" + str(round(float(coordinate[1]) * (maxBounds[1] - minBounds[1]) + minBounds[1], 5)) + "\"/>\n"
        output += "    </trkseg>\n  </trk>\n"

    output += "</gpx>"
    
    with open("output.gpx", "w") as file:
        file.write(output)
    print("success!")
        
#llm_output = "[[(1.0, 0.05008), (0.83275, 0.39733), (0.77544, 0.36728), (0.50761, 0.52421), (0.26784, 0.76461), (0.08889, 1.0), (0.0, 0.86811), (0.37077, 0.29716), (0.44679, 0.19366), (0.88655, 0.0), (1.0, 0.05008)]]"
llm_output = "[[(0.39329, 0.37594), (0.41266, 0.25955), (0.42023, 0.17569), (0.42287, 0.02477)], [(0.48417, 0.33377), (0.50214, 0.17277), (0.50455, 0.10088), (0.50193, 0.04901)], [(0.73937, 0.15647), (0.73597, 0.11644), (0.7356, 0.08354), (0.74082, 0.02954)], [(0.90359, 0.02184), (0.79163, 0.04002), (0.61034, 0.08314), (0.50455, 0.10088), (0.42023, 0.17569), (0.39329, 0.37594), (0.38029, 0.51984), (0.37754, 0.56275), (0.37505, 0.64418), (0.37885, 0.70015), (0.39287, 0.75693), (0.41221, 0.79872)], [(0.03575, 0.93155), (0.08987, 0.86873), (0.0977, 0.85843), (0.2608, 0.61282)], [(0.28716, 0.57041), (0.2608, 0.61282), (0.16981, 0.73371), (0.0977, 0.85843)]]"
convert_to_gpx((46.72532, -117.17138), (46.72818, -117.16845), llm_output)