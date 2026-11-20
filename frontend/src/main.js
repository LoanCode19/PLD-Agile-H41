import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { displayJson } from './display.js';

document.querySelector('#app').innerHTML = `
  <button id="bouton">Afficher</button>
  <pre id="zone"></pre>
  <h2>Carte de Lyon</h2>
  <div id="map" style="height: 500px;"></div>
`;

const bouton = document.getElementById('bouton');
const zone = document.getElementById('zone');

// Au clic, on affiche le JSON (en dur pour l'instant)
bouton.addEventListener('click', () => {
    fetch('http://localhost:8000/api/route-graph')
        .then(response => response.json())
        .then(data => displayJson(data, zone));
});
// Initialisation de la carte de Lyon
const map = L.map('map').setView([45.7640, 4.8357], 13);

// Fond de carte OpenStreetMap
L.tileLayer(
  'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }
).addTo(map);