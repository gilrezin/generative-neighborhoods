/* global L */
const map = L.map('map').setView([46.73, -117.16], 15);           // Pullman default
window.gpxLayer = null;  // Track the GPX overlay globally
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

// Function to display a set of nodes as GPX on the map
function displayNodesAsGPX(nodes) {
  // Create a GPX string from the nodes
  const gpxString = generateGPXFromNodes(nodes);
  
  // If there's an existing GPX layer, remove it
  if (window.gpxLayer) {
    map.removeLayer(window.gpxLayer);
  }
  
  // Create a Blob from the GPX string
  const blob = new Blob([gpxString], {type: 'application/gpx+xml'});
  const url = URL.createObjectURL(blob);
  
  // Load the GPX from the object URL
  window.gpxLayer = new L.GPX(url, {
    async: true,
    polyline_options: {
      color: "blue",
      weight: 4,
      opacity: 0.75,
      lineJoin: "round"
    }
  })
  .on("loaded", function(e) {
    map.fitBounds(e.target.getBounds());
    console.log("✅ Generated GPX track displayed successfully.");
    // Clean up the URL object
    URL.revokeObjectURL(url);
  })
  .on("error", function(e) {
    console.error("Error loading GPX:", e);
  })
  .addTo(map);
}

// Function to generate GPX XML from an array of nodes
function generateGPXFromNodes(nodes) {
  // Create GPX header
  let gpxContent = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Polygon to Street Demo" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Generated Track</name>
    <trkseg>`;
  
  // Add each node as a trackpoint
  nodes.forEach(node => {
    gpxContent += `
      <trkpt lat="${node[0]}" lon="${node[1]}">
        <ele>0</ele>
      </trkpt>`;
  });
  
  // Close GPX tags
  gpxContent += `
    </trkseg>
  </trk>
</gpx>`;
  
  return gpxContent;
}

// Add a function to fetch and display nodes from your backend
async function fetchAndDisplayNodes() {
  try {
    const response = await fetch('http://127.0.0.1:5050/api/get_nodes');
    const data = await response.json();
    
    if (data.nodes && Array.isArray(data.nodes)) {
      displayNodesAsGPX(data.nodes);
      document.getElementById('output').textContent = "Loaded " + data.nodes.length + " nodes";
    } else {
      document.getElementById('output').textContent = "No valid nodes received from server";
    }
  } catch (error) {
    console.error("Error fetching nodes:", error);
    document.getElementById('output').textContent = "Error: " + error.message;
  }
}

// Add a button to your HTML
document.addEventListener('DOMContentLoaded', function() {
  const loadNodesBtn = document.createElement('button');
  loadNodesBtn.id = 'loadNodesBtn';
  loadNodesBtn.textContent = 'Load Nodes from Server';
  loadNodesBtn.style.marginTop = '10px';
  
  const submitBtn = document.getElementById('submitBtn');
  submitBtn.parentNode.insertBefore(loadNodesBtn, submitBtn.nextSibling);
  
  loadNodesBtn.addEventListener('click', fetchAndDisplayNodes);
});

// Add a text area for manual node input
document.addEventListener('DOMContentLoaded', function() {
  const nodeInputArea = document.createElement('textarea');
  nodeInputArea.id = 'nodeInput';
  nodeInputArea.placeholder = 'Enter nodes as JSON array: [[lat1, lng1], [lat2, lng2], ...] or LLM tuple format';
  nodeInputArea.rows = 4;
  nodeInputArea.style.width = '100%';
  nodeInputArea.style.marginTop = '10px';
  
  const displayNodesBtn = document.createElement('button');
  displayNodesBtn.id = 'displayNodesBtn';
  displayNodesBtn.textContent = 'Display Nodes';
  displayNodesBtn.style.marginTop = '10px';
  
  const output = document.getElementById('output');
  output.parentNode.insertBefore(nodeInputArea, output);
  output.parentNode.insertBefore(displayNodesBtn, output);
  
  // Replace the existing click handler with this improved one
  displayNodesBtn.addEventListener('click', function() {
    try {
      const nodesText = document.getElementById('nodeInput').value;
      let nodes;
      
      // Try parsing as JSON first
      try {
        nodes = JSON.parse(nodesText);
      } catch (e) {
        // If JSON parsing fails, try parsing as tuple format
        if (nodesText.trim().startsWith("[[") && nodesText.includes("(")) {
          // This looks like tuple format
          // Extract the content between the outer brackets
          let content = nodesText.trim().slice(2, -2);
          
          // Split by "), ("
          let pairs = content.split("), (");
          
          // Convert each pair to array format
          nodes = pairs.map(pair => {
            // Remove any remaining parentheses
            pair = pair.replace(/\(/g, '').replace(/\)/g, '');
            // Split by comma and convert to numbers
            return pair.split(',').map(num => parseFloat(num.trim()));
          });
        } else {
          throw e; // Re-throw if it's not the tuple format
        }
      }
      
      if (Array.isArray(nodes) && nodes.length > 0 && Array.isArray(nodes[0])) {
        displayNodesAsGPX(nodes);
        document.getElementById('output').textContent = "Displayed " + nodes.length + " nodes";
      } else {
        document.getElementById('output').textContent = "Invalid node format. Use [[lat1, lng1], [lat2, lng2], ...] or tuple format";
      }
    } catch (error) {
      console.error("Error parsing nodes:", error);
      document.getElementById('output').textContent = "Error parsing nodes: " + error.message;
    }
  });
});
