/* global L */
const map = L.map('map').setView([46.73, -117.16], 15);           // Pullman default
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
}).addTo(map);

const drawnItems = new L.FeatureGroup().addTo(map);
const drawControl = new L.Control.Draw({
  draw: { polygon: true, polyline: false, circle: false, rectangle: false, marker: false, circlemarker: false },
  edit: { featureGroup: drawnItems }
});
map.addControl(drawControl);

let latestPolygon = null;

map.on(L.Draw.Event.CREATED, (e) => {
  if (latestPolygon) drawnItems.removeLayer(latestPolygon);
  latestPolygon = e.layer;
  drawnItems.addLayer(latestPolygon);
  document.getElementById('submitBtn').disabled = false;
});

document.getElementById('submitBtn').addEventListener('click', async () => {
  if (!latestPolygon) return;
  const coords = latestPolygon.getLatLngs()[0].map(ll => [ll.lat, ll.lng]);

  const res = await fetch('http://127.0.0.1:5050/api/submit_polygon', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ polygon: coords, returnPrompt: true })
  });

  const data = await res.json();
  document.getElementById('output').textContent = JSON.stringify(data, null, 2);
});
