/* global L */
document.addEventListener('DOMContentLoaded', () => {

  /* ---------- Base Leaflet map ---------- */
  const map = L.map('map').setView([46.73, -117.16], 15);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
  
  /* ---------- Draw-a-polygon & submit ---------- */
  const drawnItems = new L.FeatureGroup().addTo(map);
  const drawControl = new L.Control.Draw({
    draw : { polygon:true, rectangle:false, marker:false, circle:false,
             circlemarker:false, polyline:false },
    edit : { featureGroup: drawnItems }
  });
  map.addControl(drawControl);
  
  let latestPolygon=null;
  map.on(L.Draw.Event.CREATED, e=>{
    if (latestPolygon) drawnItems.removeLayer(latestPolygon);
    latestPolygon = e.layer;
    drawnItems.addLayer(latestPolygon);
    document.getElementById('submitBtn').disabled = false;
  });
  
  // Submit button event action
  document.getElementById('submitBtn').addEventListener('click', async (e)=>{
    e.preventDefault();
    if(!latestPolygon) return;
    const coords = latestPolygon.getLatLngs()[0].map(ll=>[ll.lat, ll.lng]);

    // timeout after 60s of waiting for server
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    // call backend
    try
    {
      const res = await fetch('http://127.0.0.1:5050/api/submit_polygon',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ polygon:coords, returnPrompt:true }),
        signal: controller.signal
      });
      if (!res.ok) { // If server returns 4xx or 5xx
        throw new Error(`Server error: ${res.status}`);
      }
      const data = await res.json();
      console.log(data)
      // parse LLM output
      document.getElementById('output').textContent =
          JSON.stringify(data,null,2);
      document.getElementById('nodeInput').value = data[0].toString();
      document.getElementById('minLat').value = data[1][0].toString();
      document.getElementById('minLng').value = data[1][1].toString();
      document.getElementById('maxLat').value = data[1][2].toString();
      document.getElementById('maxLng').value = data[1][3].toString();
      document.getElementById('displayNodesBtn').click();
    }
    catch (err)
    {
      console.error('Error retrieving output:', err);
      document.getElementById('output').textContent = 'Error retrieving output.';
    }
    
  });
  
  /* ---------- GPX file upload ---------- */
  let gpxLayer=null;
  document.getElementById('gpxUpload').addEventListener('change', e=>{
    const file = e.target.files[0]; if(!file) return;
    const rdr = new FileReader();
    rdr.onload = ev=>{
      if (gpxLayer) map.removeLayer(gpxLayer);
      gpxLayer = new L.GPX(ev.target.result,{ async:true,
        polyline_options:{ color:'red', weight:4, opacity:0.75 }})
        .on('loaded', e2=> map.fitBounds(e2.target.getBounds()) )
        .addTo(map);
    };
    rdr.readAsText(file);
  });
  
  /* ---------- LLM normalized nodes to geographic ---------- */
// function that converts relative (0-1) pairs to real lat/lng
function toLatLngPair([relLat, relLng], minLat, minLng, maxLat, maxLng) {
  const lat = relLat * (maxLat - minLat) + minLat;   // same math used in convert_to_gpx.py :contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}
  const lng = relLng * (maxLng - minLng) + minLng;
  return [lat, lng];
}

// Display Nodes button event
document
  .getElementById("displayNodesBtn")
  .addEventListener("click", () => {
    // -------- grab & sanity-check the raw text area  --------
    let raw = document.getElementById("nodeInput").value.trim();
    if (!raw) return alert("Paste the model’s output first!");

    // the model sometimes gives `(x, y)` pairs – turn them into JSON
    raw = raw.replaceAll("(", "[").replaceAll(")", "]");

    let lines;
    try {
      lines = JSON.parse(raw);           // expecting  [ [ [x,y], …], [ [x,y], …] ]
    } catch (e) {
      return alert("Couldn’t parse the text as JSON.\n" + e);
    }

    // -------- pull the bounding-box the user typed in  --------
    const minLat = parseFloat(document.getElementById("minLat").value);
    const minLng = parseFloat(document.getElementById("minLng").value);
    const maxLat = parseFloat(document.getElementById("maxLat").value);
    const maxLng = parseFloat(document.getElementById("maxLng").value);

    // -------- draw every inner array as a polyline  --------
    // (clear old preview first)
    if (window.__llmPreviewGroup) map.removeLayer(window.__llmPreviewGroup);

    const layerGroup = L.featureGroup().addTo(map);
    window.__llmPreviewGroup = layerGroup;

    lines.forEach((lineArr, idx) => {
      // skip if all points are the same
      const uniq = [...new Set(lineArr.map(JSON.stringify))];
      if (uniq.length < 2) return;
    
      const latLngs = lineArr.map(pt =>
        toLatLngPair(pt, minLat, minLng, maxLat, maxLng)
      );
    
      L.polyline(latLngs, { color: "red", weight: 3 }).addTo(layerGroup);
    });
    

    // optional: fit map to the drawn result
    if (layerGroup.getLayers().length) {
      map.fitBounds(layerGroup.getBounds().pad(0.2));
    }
  });

  });
  