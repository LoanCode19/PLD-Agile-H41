import { displayLivraisons } from './displayLivraisons.js';
import { displayTournees } from './displayTournees.js';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

document.querySelector('#app').innerHTML = `
  <div style="margin-bottom: 20px;">
    <input type="file" id="fileInputLivraison" />
    <button id="bouton-livraisons">Uploader les livraisons</button>
    <br><br>
    <input type="file" id="fileInputCarte" />
    <button id="bouton-carte">Uploader la carte</button>
    <p id="statut" style="font-weight: bold; color: #333;"></p>
  </div>

  <button id="bouton-tournees">Afficher les tournées</button>

  <div id="zone-tournees"></div>
  <h2>Carte de Lyon</h2>
  <div id="map" style="height: 500px;"></div>

  <section>
    <h2>Liste des livraisons</h2>
    <div id="livraisons"></div>
  </section>
`;

const fileInputLivraison = document.getElementById('fileInputLivraison');
const boutonLivraisons = document.getElementById('bouton-livraisons');
const fileInputCarte = document.getElementById('fileInputCarte');
const boutonCarte = document.getElementById('bouton-carte');
const statut = document.getElementById('statut');

boutonLivraisons.addEventListener('click', () => {
  if (fileInputLivraison.files.length === 0) {
    statut.textContent = "Veuillez d'abord sélectionner un fichier de livraisons.";
    return;
  }
  const formData = new FormData();
  formData.append('file', fileInputLivraison.files[0]);
  
  statut.textContent = "Upload des livraisons en cours...";
  fetch('http://localhost:8000/api/upload-livraisons', {
    method: 'POST',
    body: formData
  })
    .then(response => {
      if (response.ok) {
        statut.textContent = "Fichier livraisons uploadé avec succès !";
      } else {
        statut.textContent = "Erreur lors de l'upload des livraisons.";
      }
    })
    .catch(error => {
      statut.textContent = `Erreur réseau : ${error}`;
    });
});

boutonCarte.addEventListener('click', () => {
  if (fileInputCarte.files.length === 0) {
    statut.textContent = "Veuillez d'abord sélectionner un fichier de carte.";
    return;
  }
  const formData = new FormData();
  formData.append('file', fileInputCarte.files[0]);
  
  statut.textContent = "Upload de la carte en cours...";
  fetch('http://localhost:8000/api/upload-carte', {
    method: 'POST',
    body: formData
  })
    .then(response => {
      if (response.ok) {
        statut.textContent = "Fichier carte uploadé avec succès !";
      } else {
        statut.textContent = "Erreur lors de l'upload de la carte.";
      }
    })
    .catch(error => {
      statut.textContent = `Erreur réseau : ${error}`;
    });
});

const map = L.map('map').setView([45.7640, 4.8357], 13);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const tourneeLayer = L.layerGroup().addTo(map);

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