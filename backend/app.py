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

jobs = {}

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

    if body.get("returnPrompt"):
        poly = Polygon(coords_tuples)
        prompt, bounds = polygon_to_prompt(poly, streets)

        # call the LLM with the prompt
        tuned_models = list(client.tunings.list())
        newest_model = tuned_models[len(tuned_models) - 1]

        response = client.models.generate_content(
            model=newest_model.name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0)
        )

        llm_output = response.text
        # fix any broken output
        if (llm_output.count('[') != llm_output.count(']')):
            llm_output = llm_output[:llm_output.rfind(")")] + ']]'

    return jsonify(llm_output, bounds), 200

async def get_streets(coords_tuples):
    return await streets_intersecting_polygon(coords_tuples)


if __name__ == "__main__":
    # `python -m backend.app` also works
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False)
