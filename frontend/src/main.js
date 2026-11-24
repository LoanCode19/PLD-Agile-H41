import { displayLivraisons } from './displayLivraisons.js';
import { displayTournees } from './displayTournees.js';
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

// Initialisation de la carte de Lyon
const map = L.map('map').setView([45.7640, 4.8357], 13);

// Fond de carte OpenStreetMap
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Couche dédiée aux tournées : on peut la vider/redessiner sans toucher
// au fond de carte.
const tourneeLayer = L.layerGroup().addTo(map);

document.getElementById('bouton').addEventListener('click', async () => {
  try {
    const response = await fetch('http://localhost:8080/api/route-graph');
    const data = await response.json();

    displayJson(data, document.getElementById('zone'));
  } catch (error) {
    document.getElementById('zone').textContent =
      `Erreur : ${error.message}`;
  }
});

// La tournée vient de l'API : on lance la requête à chaque clic pour
// récupérer un résultat à jour.
const boutonTournees = document.getElementById('bouton-tournees');
const zoneTournees = document.getElementById('zone-tournees');
boutonTournees.addEventListener('click', () => {
  fetch('http://localhost:8080/api/getTestShortestPath')
    .then(response => response.json())
    .then(data => displayTournees(data, tourneeLayer, zoneTournees))
    .catch(() => {
      zoneTournees.textContent =
        'Erreur : impossible de contacter l\'API (backend démarré ?)';
    });
});

async function loadLivraisons() {
  const zone = document.getElementById('livraisons');

  try {
    const response = await fetch(
      'http://127.0.0.1:8080/api/getTestListLivraison'
    );

    const data = await response.json();

    if (!response.ok) {
      displayLivraisons(data, zone);
      return;
    }

    displayLivraisons(data, zone);
  } catch (error) {
    zone.textContent =
      `Erreur lors du chargement des livraisons : ${error.message}`;
  }
}

loadLivraisons();
