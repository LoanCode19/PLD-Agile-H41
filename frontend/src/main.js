import { displayLivraisons } from './displayLivraisons.js';
import { displayTournees } from './displayTournees.js';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const API = 'http://localhost:8080/api';

// === Gestion centralisée des erreurs ===
export class ErreurApi extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

export async function appelerApi(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new ErreurApi('RESEAU', "Impossible de contacter l'API (backend démarré ?)");
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const e = data?.erreur;
    throw new ErreurApi(
      e?.code ?? 'INCONNUE',
      e?.message ?? `Erreur ${response.status}`,
      e?.details
    );
  }
  return data;
}

function afficherErreur(e, zoneAffichage) {
  if (!(e instanceof ErreurApi)) {
    zoneAffichage.textContent = 'Erreur inconnue';
    return;
  }
  zoneAffichage.textContent = `Erreur : ${e.message}`;
  zoneAffichage.style.color = '#d32f2f';
}

document.querySelector('#app').innerHTML = `
  <div style="margin-bottom: 20px;">
    1. <input type="file" id="fileInputCarte" accept=".xml" />
    <button id="bouton-carte">Uploader la carte</button>
    <br><br>
    2. <input type="file" id="fileInputLivraison" accept=".xml" />
    <button id="bouton-livraisons" disabled>Uploader les livraisons</button>
    <p id="statut" style="font-weight: bold; color: #333;">Commencez par uploader une carte.</p>
  </div>

  <button id="bouton-tournees" disabled>Afficher les tournées</button>

  <div id="zone-tournees"></div>
  <h2>Carte de Lyon</h2>
  <div id="map" style="height: 500px;"></div>

  <section>
    <h2>Liste des livraisons</h2>
    <div id="livraisons">Aucune livraison chargée.</div>
  </section>
`;

const fileInputCarte = document.getElementById('fileInputCarte');
const boutonCarte = document.getElementById('bouton-carte');
const fileInputLivraison = document.getElementById('fileInputLivraison');
const boutonLivraisons = document.getElementById('bouton-livraisons');
const boutonTournees = document.getElementById('bouton-tournees');
const statut = document.getElementById('statut');
const zoneTournees = document.getElementById('zone-tournees');
const zoneLivraisons = document.getElementById('livraisons');

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

// Efface la tournée affichée (elle n'est plus valable si un fichier change).
function effacerTournee() {
  tourneeLayer.clearLayers();
  zoneTournees.replaceChildren();
}

// Envoie le fichier choisi dans `input` à l'API (champ "file").
// Renvoie le JSON de la réponse, ou lance une ErreurApi en cas d'erreur.
async function uploader(input, url) {
  if (input.files.length === 0) {
    throw new ErreurApi('FICHIER_MANQUANT', "Veuillez d'abord sélectionner un fichier.");
  }
  const formData = new FormData();
  formData.append('file', input.files[0]);
  statut.textContent = 'Upload en cours...';

  const formData2 = new FormData();
  formData2.append('file', input.files[0]);
  return appelerApi(url, { method: 'POST', body: formData2 });
}

// 1. Carte : une nouvelle carte oublie les livraisons précédentes.
boutonCarte.addEventListener('click', async () => {
  try {
    const data = await uploader(fileInputCarte, `${API}/upload-carte`);
    effacerTournee();
    zoneLivraisons.textContent = 'Aucune livraison chargée.';
    boutonLivraisons.disabled = false;
    boutonTournees.disabled = true;
    statut.textContent =
      `Carte chargée (${data.intersections} intersections). Uploadez maintenant les livraisons.`;
    statut.style.color = '#333';
  } catch (e) {
    afficherErreur(e, statut);
  }
});

// 2. Livraisons : affichées en bas de la page.
boutonLivraisons.addEventListener('click', async () => {
  try {
    const data = await uploader(fileInputLivraison, `${API}/upload-livraisons`);
    effacerTournee();
    displayLivraisons(data, zoneLivraisons);
    boutonTournees.disabled = false;
    statut.textContent = 'Livraisons chargées. Vous pouvez afficher la tournée.';
    statut.style.color = '#333';
  } catch (e) {
    afficherErreur(e, statut);
    // En cas d'erreur le backend n'a plus de livraisons chargées.
    zoneLivraisons.textContent = 'Aucune livraison chargée.';
    boutonTournees.disabled = true;
  }
});

// 3. Tournée : calculée par l'API à partir de la carte et des livraisons uploadées.
boutonTournees.addEventListener('click', async () => {
  try {
    const data = await appelerApi(`${API}/tournee`);
    displayTournees(data, tourneeLayer, zoneTournees);
    statut.textContent = 'Tournée affichée.';
    statut.style.color = '#333';
  } catch (e) {
    afficherErreur(e, zoneTournees);
    if (e.code === 'ETAT_INVALIDE') {
      boutonTournees.disabled = true;
    }
  }
});
