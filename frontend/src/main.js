import { displayLivraisons } from './displayLivraisons.js';
import demandeTournees from './demandeTournees.json';
import { displayTournees } from './displayTournees.js';
import livraisonsExemple from './livraisonsExemple.json';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { displayJson } from './display.js';

document.querySelector('#app').innerHTML = `
  <button id="bouton">Afficher</button>
  <button id="bouton-tournees">Afficher les tournées</button>
  <pre id="zone"></pre>
  <div id="zone-tournees"></div>
  <h2>Carte de Lyon</h2>
  <div id="map" style="height: 500px;"></div>
<section>
  <h2>Liste des livraisons</h2>
  <div id="livraisons"></div>
</section>
`;

const bouton = document.getElementById('bouton');
const zone = document.getElementById('zone');

// Au clic, on affiche le JSON (en dur pour l'instant)
bouton.addEventListener('click', () => {
    fetch('http://localhost:8080/api/route-graph')
        .then(response => response.json())
        .then(data => displayJson(data, zone));
});

// La donnée vient de demandeTournees.json (import en haut du fichier).
// Quand l'API sera prête, remplacer par :
//   boutonTournees.addEventListener('click', () => {
//       fetch('http://localhost:8080/api/demande-de-tournees')
//           .then(response => response.json())
//           .then(data => displayTournees(data, tourneeLayer, zoneTournees));
//   });
const boutonTournees = document.getElementById('bouton-tournees');
const zoneTournees = document.getElementById('zone-tournees');
// Initialisation de la carte de Lyon
const map = L.map('map').setView([45.7640, 4.8357], 13);

// Couche dédiée aux tournées : on peut la vider/redessiner sans toucher
// au fond de carte.
const tourneeLayer = L.layerGroup().addTo(map);

boutonTournees.addEventListener('click', () => {
    displayTournees(demandeTournees, tourneeLayer, zoneTournees);
});

// Fond de carte OpenStreetMap
L.tileLayer(
  'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }
).addTo(map);
displayLivraisons(
  livraisonsExemple,
  document.getElementById('livraisons')
);