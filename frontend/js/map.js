/* global L */
document.addEventListener('DOMContentLoaded', () => {

  /* ---------- 1. Base Leaflet map ---------- */
  const map = L.map('map').setView([46.73, -117.16], 15);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
  
  /* ---------- 2. Draw-a-polygon & submit ---------- */
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
  
  document.getElementById('submitBtn').addEventListener('click', async ()=>{
    if(!latestPolygon) return;
    const coords = latestPolygon.getLatLngs()[0].map(ll=>[ll.lat, ll.lng]);
    const res = await fetch('http://127.0.0.1:5050/api/submit_polygon',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ polygon:coords, returnPrompt:true })
    });
    const data = await res.json();
    document.getElementById('output').textContent =
        JSON.stringify(data,null,2);
  });
  
  /* ---------- 3. GPX file upload ---------- */
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
  
  /* ---------- 4. LLM normalized nodes → geographic ---------- */
  function parseLLMFormat(txt){
    // strip outer [[...]] then split on "), ("
    const inner = txt.trim().replace(/^\[\[/,'').replace(/\]\]$/,'');
    return inner.split(/\),\s*\(/).map(pair=>{
      const [x,y]=pair.replace(/[()]/g,'').split(',').map(Number);
      return [x,y];
    });
  }
  function scaleToGeo(normCoords, minLat, minLng, maxLat, maxLng) {
    return normCoords.map(([dLat, dLng]) => [
      minLat + dLat * (maxLat - minLat),   // 1st value = latitude offset
      minLng + dLng * (maxLng - minLng)    // 2nd value = longitude offset
    ]);
  }
  
  document.getElementById('displayNodesBtn').addEventListener('click', ()=>{
    const raw   = document.getElementById('nodeInput').value;
    const minLat= parseFloat(document.getElementById('minLat').value);
    const minLng= parseFloat(document.getElementById('minLng').value);
    const maxLat= parseFloat(document.getElementById('maxLat').value);
    const maxLng= parseFloat(document.getElementById('maxLng').value);
    try{
      const norm = parseLLMFormat(raw);
      const geo  = scaleToGeo(norm,minLat,minLng,maxLat,maxLng);
      L.polyline(geo,{ color:'blue', weight:4, opacity:0.8 }).addTo(map);
      map.fitBounds(geo);
      document.getElementById('output').textContent =
        `Displayed ${geo.length} nodes (scaled to geo).`;
    }catch(err){
      console.error(err);
      document.getElementById('output').textContent='❌ parse error';
    }
  });
  
  });
  