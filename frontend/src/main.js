import { displayLivraisons, lireAssignations } from './displayLivraisons.js';
import { displayTournees, displayPointsNonAssignes } from './displayTournees.js';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { setupLivreurs } from './displayLivreurs.js';
import { API, ErreurApi, appelerApi } from './api.js';

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
    <p id="statut" style="font-weight: bold; color: #333;">Commencez par uploader une carte.</p>
    1. Uploader la carte : <input type="file" id="fileInputCarte" accept=".xml" />
    <br><br>
    2. Uploader les livraisons : <input type="file" id="fileInputLivraison" accept=".xml" />
    <div id="erreur-livraisons" style="color: red; font-size: 15px; margin-top: 4px;"></div>
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
const fileInputLivraison = document.getElementById('fileInputLivraison');
const boutonTournees = document.getElementById('bouton-tournees');
const statut = document.getElementById('statut');
const zoneTournees = document.getElementById('zone-tournees');
const zoneLivraisons = document.getElementById('livraisons');
const erreurLivraisons = document.getElementById('erreur-livraisons');
let carteChargee = false;

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
// Renvoie le JSON de la réponse, ou lance une ErreurApi en cas d'erreur.
// (les gestionnaires 'change' ne l'appellent que si un fichier est choisi)
async function uploader(input, url) {
  const formData = new FormData();
  formData.append('file', input.files[0]);
  statut.textContent = 'Upload en cours...';
  return appelerApi(url, { method: 'POST', body: formData });
}

// Réaffiche la liste des livraisons avec les coursiers donnés
// (rien à faire tant qu'aucune livraison n'est chargée).
function afficherLivraisons(coursiers) {
  if (demandeCourante) displayLivraisons(demandeCourante, coursiers, zoneLivraisons);
}

// 1. Carte : l'upload part dès qu'un fichier est choisi.
// Une nouvelle carte oublie les livraisons précédentes.
fileInputCarte.addEventListener('change', async () => {
  if (fileInputCarte.files.length === 0) return; // l'utilisateur a annulé la sélection du fichier

  try {
    const data = await uploader(fileInputCarte, `${API}/upload-carte`);
    carteChargee = true;
    erreurLivraisons.textContent = '';
    effacerTournee();
    demandeCourante = null;
    zoneLivraisons.textContent = 'Aucune livraison chargée.';
    fileInputLivraison.value = ''; // réinitialise le champ pour forcer l'utilisateur à re-sélectionner un fichier
    boutonTournees.disabled = true;
    statut.textContent =
      `Carte chargée (${data.intersections} intersections). Uploadez maintenant les livraisons.`;
    statut.style.color = '#333';
  } catch (e) {
    // Carte refusée : le backend garde l'ancienne carte (s'il y en avait une),
    // donc carteChargee ne change pas.
    afficherErreur(e, statut);
    fileInputCarte.value = ''; // pour que re-choisir le même fichier (corrigé) relance l'upload
  }
});

// 2. Livraisons : l'upload part dès qu'un fichier est choisi ; affichées en
// bas de la page, avec un choix de coursier pour chacune. Le backend a effacé
// les anciennes assignations.
fileInputLivraison.addEventListener('change', async () => {
  if (fileInputLivraison.files.length === 0) return; // l'utilisateur a annulé la sélection du fichier

  // Vérification côté front pour éviter un appel inutile (le backend
  // répondrait de toute façon CARTE_NON_CHARGEE).
  if (!carteChargee) {
    erreurLivraisons.textContent = "Veuillez d'abord uploader la carte.";
    fileInputLivraison.value = ''; // vide le champ pour que l'utilisateur puisse réessayer
    return;
  }
  erreurLivraisons.textContent = '';

  effacerTournee();
  zoneLivraisons.replaceChildren(); // les anciens choix ne valent plus
  try {
    demandeCourante = await uploader(fileInputLivraison, `${API}/upload-livraisons`);
  } catch (e) {
    afficherErreur(e, statut);
    // En cas d'erreur le backend n'a plus de livraisons chargées.
    demandeCourante = null;
    zoneLivraisons.textContent = 'Aucune livraison chargée.';
    boutonTournees.disabled = true;
    fileInputLivraison.value = ''; // pour que re-choisir le même fichier (corrigé) relance l'upload
    return;
  }

  try {
    afficherLivraisons(await appelerApi(`${API}/coursiers`));
  } catch (e) {
    afficherErreur(e, statut);
    return;
  }
  boutonTournees.disabled = false;
  statut.textContent =
    'Livraisons chargées. Choisissez un coursier pour chacune, puis calculez les tournées.';
  statut.style.color = '#333';
});

// 3. Calcul : on envoie les choix des listes déroulantes au backend
// (on vide toutes les assignations, puis on assigne coursier par coursier),
// puis on affiche les tournées qu'il a calculées et, en gris, les livraisons
// sans coursier. Sans aucune assignation, on passe quand même par le vidage
// (le backend peut garder des assignations d'un calcul précédent) : on ne
// voit alors que les points gris.
boutonTournees.addEventListener('click', async () => {
  const assignations = lireAssignations(zoneLivraisons);

  boutonTournees.disabled = true;
  statut.textContent = 'Calcul des tournées en cours...';
  try {
    // Le vidage doit être terminé avant les assignations (await).
    await appelerApi(`${API}/deleteAllLivraisonsForCoursiers`, { method: 'DELETE' });
    for (const [idCoursier, idsLivraisons] of assignations) {
      await appelerApi(`${API}/coursiers/${idCoursier}/assignLivraisons`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(idsLivraisons)
      });
    }
    displayTournees(await appelerApi(`${API}/tournee`), tourneeLayer, zoneTournees);
    displayPointsNonAssignes(await appelerApi(`${API}/points-non-assignes`), tourneeLayer, zoneTournees);
    statut.textContent = assignations.size === 0
      ? 'Aucune livraison assignée : seules les livraisons non assignées sont affichées.'
      : 'Tournées calculées.';
    statut.style.color = '#333';
    boutonTournees.disabled = false;
  } catch (e) {
    // Une partie des assignations a pu être faite : on n'affiche rien de faux.
    effacerTournee();
    afficherErreur(e, zoneTournees);
    // Le backend n'a plus de carte ou de livraisons : rien à recalculer tant
    // qu'on ne les a pas (re)chargées.
    const plusDeDonnees = e.code === 'CARTE_NON_CHARGEE' || e.code === 'LIVRAISONS_NON_CHARGEES';
    boutonTournees.disabled = plusDeDonnees;
  }
});

// Quand les livreurs changent, les listes déroulantes sont mises à jour
// (les choix en cours sont gardés).
setupLivreurs(document.getElementById('livreurs'), { onChange: afficherLivraisons });
