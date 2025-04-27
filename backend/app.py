"""
Flask backend for Polygon‑to‑Street‑list demo
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from shapely.geometry import Polygon
from street_utils import streets_intersecting_polygon
from form_prompt import polygon_to_prompt   # your existing helper
from google import genai
from google.genai import types

client = genai.Client(api_key='AIzaSyDZRso0rXXUwsMSnoFVYeLVOLwPqIZsZKk')

app = Flask(__name__)
CORS(app)    # allow requests from localhost file:// or any domain while testing

@app.route("/api/submit_polygon", methods=["POST"])
def submit_polygon():
    """
    Expected JSON:
    {
      "polygon": [
        [lat1, lon1],
        [lat2, lon2],
        ...
      ],
      "returnPrompt": true   # optional – default False
    }
    """
    body = request.get_json(force=True)
    coords = body.get("polygon", [])

    if len(coords) < 3:
        return jsonify({"error": "Need at least 3 coordinate pairs"}), 400

    try:
        coords_tuples = [(float(lat), float(lon)) for lat, lon in coords]
    except (ValueError, TypeError):
        return jsonify({"error": "Coordinates must be [[lat, lon], ...]"}), 400

    streets = streets_intersecting_polygon(coords_tuples)

    response = {"streets": streets}

    if body.get("returnPrompt"):                           # optional
        poly = Polygon(coords_tuples)
        prompt = polygon_to_prompt(poly, streets)

        # call the LLM with the prompt
        #print(prompt + "\nGenerating...")
        tuned_models = list(client.tunings.list())
        newest_model = tuned_models[len(tuned_models) - 1]

        invalid_output = True
        while (invalid_output):
            response = client.models.generate_content(
                model=newest_model.name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0)
            )

            # check that the output is valid
            if (response.text.count('[') == response.text.count(']')):
                invalid_output = False

        response["prompt"] = response.text

    return jsonify(response), 200


if __name__ == "__main__":
    # `python -m backend.app` also works
    app.run(host="0.0.0.0", port=5050, debug=True)
