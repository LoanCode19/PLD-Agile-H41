
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './style.css';

// Create the application interface
document.querySelector('#app').innerHTML = `
  <h1>PLD - Optimisation des livraisons</h1>

  <div class="controls">
    <h2>Carte de Lyon</h2>
    <p>Visualisation du réseau routier</p>
  </div>
  <section class="controls">
    <h2>Charger un plan</h2>

    <input
      type="file"
      id="map-file"
      accept=".xml"
    />

    <p id="file-status">
      Aucun fichier sélectionné
    </p>
  </section>

  <div id="map"></div>
`;

// Initialize the map centered on Lyon
const map = L.map('map').setView(
  [45.7640, 4.8357],
  13
);

// Add OpenStreetMap background
L.tileLayer(
  'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }
).addTo(map);

// Example road segment (temporary test data)
const road = [
  [45.7640, 4.8357],
  [45.7650, 4.8400],
  [45.7670, 4.8420]
];

// Draw the segment
L.polyline(road, {
  color: 'blue',
  weight: 5
}).addTo(map);


const mapFileInput = document.getElementById('map-file');
const fileStatus = document.getElementById('file-status');

mapFileInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];

  if (!file) return;

  try {
    const xmlText = await file.text();

    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(
      xmlText,
      'application/xml'
    );

    const error = xmlDoc.querySelector('parsererror');

    if (error) {
      throw new Error('Invalid XML file');
    }

    console.log('XML document:', xmlDoc);

    fileStatus.textContent =
      `Fichier chargé : ${file.name}`;
  } catch (error) {
    fileStatus.textContent =
      `Erreur : ${error.message}`;
  }
});

