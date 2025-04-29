# generative-neighborhoods

WSU CS 440 Artificial Intelligence 

This application provides an end-to-end workflow for interactive geospatial storytelling: users sketch a polygon on a Leaflet map to define an area of interest, the backend then retrieves OpenStreetMap data within that region, processes the street network to identify connectivity patterns, and constructs context-rich prompts for a fine-tuned LLM. The system synthesizes raw geodata into detailed, human-readable descriptions of neighborhood character, walkability, landmark highlights, and spatial relationships.

## Features

- **Interactive Frontend**: Draw polygons on a Leaflet map and submit to backend.
- **Flask Backend API**: Exposes `/api/submit_polygon` for prompt generation and data retrieval.
- **Prompt Builder**: `form_prompt.py` constructs targeted prompts for the fine‑tuned LLM.
- **Street Network Utilities**: `street_utils.py` processes OSM street data for analysis.
- **OSM Data Ingestion**: Scripts (`getOSMFiles.py`, `getrelations.py`, `convert_to_gpx.py`) to fetch, parse, and convert OSM XML to GPX.
- **Relation ID Extraction**: `extract_relation_ids.py` aggregates relation IDs into `neighborhood_ids.txt`.
- **Batch Prompt Generation**: `generate_neighborhood_prompts.py` runs the LLM over many neighborhood IDs.

## Project Structure

```plaintext
generative-neighborhoods/
├── backend/
│   ├── app.py
│   ├── form_prompt.py
│   ├── requirements.txt
│   └── street_utils.py
├── dataset/
│   ├── getOSMFiles.py
│   └── getrelations.py
├── evaluate/
│   └── convert_to_gpx.py
├── frontend/
│   ├── index.html
│   ├── js/
│   │   └── map.js
│   └── Css/
│       └── style.css
├── overpass/
│   ├── overpass_output_data/
│   ├── extract_relation_ids.py
│   ├── generate_neighborhood_prompts.py
│   └── neighborhood_ids.txt
├── .gitignore
└── README.md
```

## Installation
[Google Collab Demo](https://colab.research.google.com/drive/1dUrVk96BRs1eNaeU7V8up1XrDMJCwqtc?usp=sharing)

### 1. Clone the repository

```bash
git clone <your-repo-url> generative-neighborhoods
cd generative-neighborhoods
```

### 2. Setup Backend

```bash
cd backend
python -m venv .venv            # Create a virtual environment
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # Install required Python packages
```

### 3. Serve Frontend

No build step required—just serve the `frontend/` directory:

- **Option A:** Open `frontend/index.html` directly in a browser.
- **Option B:** Run a simple HTTP server:
  ```bash
  cd frontend
  python -m http.server 8000
  ```
  Then visit `http://localhost:8000/index.html`.

## Usage

### Run the Backend API

```bash
cd backend
PYTHONPATH=. python app.py
```

By default, the server listens on `http://127.0.0.1:5050`.

### Open the Frontend

1. Open the map UI (see "Serve Frontend").
2. Sketch a polygon and click **Submit to backend**.
3. View JSON output (prompt, relation data, etc.) in the console panel.

### Command‑Line Scripts

#### Extract Relation IDs

Collect all relation IDs from OSM XML files:

```bash
python extract_relation_ids.py path/to/osm_files/*.osm -o neighborhood_ids.txt
```

#### Batch Prompt Generation

Generate neighborhood descriptions for each ID:

```bash
python generate_neighborhood_prompts.py \
  --input neighborhood_ids.txt \
  --output prompts.json
```

## Script Details

- **getOSMFiles.py**: Fetches OSM data using Overpass queries for specified bounding boxes.
- **getrelations.py**: Parses OSM XML to extract `<relation>` elements.
- **convert\_to\_gpx.py**: Converts OSM XML data into GPX tracks for external tools.
- **street\_utils.py**: Builds and analyzes street networks (via osmnx & geopandas).
- **form\_prompt.py**: Assembles structured prompts for the fine-tuned LLM model.
- **generate\_neighborhood\_prompts.py**: Reads `neighborhood_ids.txt`, queries the LLM, and writes JSON outputs.

## API Specification

- **Endpoint**: `POST /api/submit_polygon`
- **Request Body**: JSON with fields:
  - `polygon`: Array of `[lat, lng]` vertices.
  - `returnPrompt`: `true` to return the raw prompt string alongside analysis.
- **Response**: JSON containing keys:
  - `prompt`: The LLM prompt used.
  - `streets`: Topology or summary of streets inside the polygon.
  - `description`: Generated neighborhood description (if configured).

## Configuration

- Default host: `127.0.0.1`, port: `5050`.&#x20;
- LLM credentials and endpoint should be set in the environment or a `.env` file (not committed for security).


## Additional Resources

<<<<<<< Updated upstream
[Demo Video](https://drive.google.com/file/d/1hjGP54UIsMnjF1F6Av24EcTjigSOBPyP/view?usp=sharing)
[Presentation](https://docs.google.com/presentation/d/1XstGsTASWr0p0tD-64O3O3yrBpZUD6nb/edit?usp=sharing&ouid=114650599401108550145&rtpof=true&sd=true)
=======
Then in the terminal:
PYTHONPATH=backend python3 backend/app.py

Start liveserver through index.html


>>>>>>> Stashed changes
