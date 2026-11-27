import { displayLivraisons, lireAssignations } from './displayLivraisons.js';
import { displayTournees } from './displayTournees.js';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { setupLivreurs } from './displayLivreurs.js';

const API = 'http://localhost:8080/api';

document.querySelector('#app').innerHTML = `
  <div style="margin-bottom: 20px;">
    1. <input type="file" id="fileInputCarte" accept=".xml" />
    <button id="bouton-carte">Uploader la carte</button>
    <br><br>
    2. <input type="file" id="fileInputLivraison" accept=".xml" />
    <button id="bouton-livraisons" disabled>Uploader les livraisons</button>
    <p id="statut" style="font-weight: bold; color: #333;">Commencez par uploader une carte.</p>
  </div>

  <button id="bouton-tournees" disabled>Calculer les tournées</button>

  <div id="zone-tournees"></div>
  <h2>Carte de Lyon</h2>
  <div id="map" style="height: 500px;"></div>

  <div id="livreurs"></div>

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

// Demande renvoyée par le dernier upload de livraisons réussi (null sinon) :
// gardée pour réafficher la liste quand les livreurs changent.
let demandeCourante = null;

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
// Renvoie le JSON de la réponse, ou null en cas d'erreur (affichée dans le statut).
async function uploader(input, url) {
  if (input.files.length === 0) {
    statut.textContent = "Veuillez d'abord sélectionner un fichier.";
    return null;
  }
  const formData = new FormData();
  formData.append('file', input.files[0]);
  statut.textContent = 'Upload en cours...';

  try {
    const response = await fetch(url, { method: 'POST', body: formData });
    const data = await response.json();
    if (!response.ok) {
      statut.textContent = `Erreur : ${data.detail}`;
      return null;
    }
    return data;
  } catch (error) {
    statut.textContent = `Erreur : impossible de contacter l'API (backend démarré ?)`;
    return null;
  }
}

// Appel JSON à l'API. Renvoie le JSON de la réponse ; lève une Error avec le
// message du backend (`detail`) si la réponse n'est pas OK.
async function appelApi(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    throw new Error("impossible de contacter l'API (backend démarré ?)");
  }
  const data = await response.json();
  if (!response.ok) {
    // detail : un texte (HTTPException) ou une liste d'erreurs (validation, 422).
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
    throw new Error(detail || `erreur ${response.status}`);
  }
  return data;
}

// Réaffiche la liste des livraisons avec les coursiers donnés
// (rien à faire tant qu'aucune livraison n'est chargée).
function afficherLivraisons(coursiers) {
  if (demandeCourante) displayLivraisons(demandeCourante, coursiers, zoneLivraisons);
}

// 1. Carte : une nouvelle carte oublie les livraisons précédentes.
boutonCarte.addEventListener('click', async () => {
  const data = await uploader(fileInputCarte, `${API}/upload-carte`);
  if (!data) return;

  effacerTournee();
  demandeCourante = null;
  zoneLivraisons.textContent = 'Aucune livraison chargée.';
  boutonLivraisons.disabled = false;
  boutonTournees.disabled = true;
  statut.textContent =
    `Carte chargée (${data.intersections} intersections). Uploadez maintenant les livraisons.`;
});

// 2. Livraisons : affichées en bas de la page, avec un choix de coursier
// pour chacune. Le backend a effacé les anciennes assignations.
boutonLivraisons.addEventListener('click', async () => {
  const data = await uploader(fileInputLivraison, `${API}/upload-livraisons`);
  effacerTournee();
  zoneLivraisons.replaceChildren(); // les anciens choix ne valent plus
  if (!data) {
    // En cas d'erreur le backend n'a plus de livraisons chargées.
    demandeCourante = null;
    zoneLivraisons.textContent = 'Aucune livraison chargée.';
    boutonTournees.disabled = true;
    return;
  }

  demandeCourante = data;
  try {
    afficherLivraisons(await appelApi(`${API}/coursiers`));
  } catch (error) {
    statut.textContent = `Erreur : ${error.message}`;
    return;
  }
  boutonTournees.disabled = false;
  statut.textContent =
    'Livraisons chargées. Choisissez un coursier pour chacune, puis calculez les tournées.';
});

// 3. Calcul : on envoie les choix des listes déroulantes au backend
// (on vide toutes les assignations, puis on assigne coursier par coursier),
// puis on affiche les tournées qu'il a calculées.
boutonTournees.addEventListener('click', async () => {
  const assignations = lireAssignations(zoneLivraisons);
  if (assignations.size === 0) {
    statut.textContent =
      'Assignez au moins une livraison à un livreur (ajoutez des livreurs si la liste est vide).';
    return;
  }

  boutonTournees.disabled = true;
  statut.textContent = 'Calcul des tournées en cours...';
  try {
    // Le vidage doit être terminé avant les assignations (await).
    await appelApi(`${API}/deleteAllLivraisonsForCoursiers`, { method: 'DELETE' });
    for (const [idCoursier, idsLivraisons] of assignations) {
      await appelApi(`${API}/coursiers/${idCoursier}/assignLivraisons`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(idsLivraisons)
      });
    }
    displayTournees(await appelApi(`${API}/tournee`), tourneeLayer, zoneTournees);
    statut.textContent = 'Tournées calculées.';
  } catch (error) {
    // Une partie des assignations a pu être faite : on n'affiche rien de faux.
    effacerTournee();
    statut.textContent = `Erreur : ${error.message}`;
  } finally {
    boutonTournees.disabled = false;
  }
});

// Quand les livreurs changent, les listes déroulantes sont mises à jour
// (les choix en cours sont gardés).
setupLivreurs(document.getElementById('livreurs'), { onChange: afficherLivraisons });
