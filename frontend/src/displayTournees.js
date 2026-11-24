import L from 'leaflet';
import { formatTime } from './displayLivraisons.js';

// Icône par défaut de Leaflet (l'épingle) : il faut importer les images
// nous-mêmes, sinon elles sont introuvables une fois le code bundlé par Vite.
import iconeEpingle from 'leaflet/dist/images/marker-icon.png';
import iconeEpingle2x from 'leaflet/dist/images/marker-icon-2x.png';
import ombreEpingle from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: iconeEpingle,
  iconRetinaUrl: iconeEpingle2x,
  shadowUrl: ombreEpingle,
});

// Marqueur "E" pour l'entrepôt, bien distinct des épingles.
const iconeEntrepot = L.divIcon({
  className: 'icone-entrepot',
  html: '<div style="width:26px;height:26px;background:#1a1a2e;color:#fff;border:2px solid #fff;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:bold;box-shadow:0 0 6px rgba(0,0,0,.5);">E</div>',
  iconSize: [26, 26],
  iconAnchor: [13, 13],
  popupAnchor: [0, -14],
});

// Une couleur par coursier (on reboucle si on dépasse la liste).
const COULEURS = ['#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#008080', '#9a6324', '#800000'];

// Dessine la tournée du (ou des) coursier(s) sur la carte.
// L'API renvoie un Coursier (ou un tableau de Coursiers) :
// {
//   id, nom, prenom, livraisons: [...],
//   tournee: {
//     chemin: [ { adresse, latitude, longitude, type, livraison, heure_arrivee, heure_depart } ],
//     depasse_heure_max: true/false
//   }
// }
// type vaut "entrepot", "enlevement", "livraison" ou "passage" ;
// les heures sont en secondes après minuit (null pour un simple passage).
export function displayTournees(data, coucheTournees, zone) {
  coucheTournees.clearLayers();
  zone.replaceChildren();

  // Erreur renvoyée par l'API ({ detail: "..." }) ou réponse vide.
  if (!data || data.detail) {
    zone.textContent = `Erreur : ${data?.detail ?? "aucune réponse de l'API"}`;
    return;
  }

  const coursiers = (Array.isArray(data) ? data : [data])
    .filter(c => c?.tournee?.chemin?.length > 0);

  if (coursiers.length === 0) {
    zone.textContent = 'Aucune tournée calculée.';
    return;
  }

  // L'entrepôt est commun à tous les coursiers : on ne le dessine qu'une fois.
  let entrepotAffiche = false;

  coursiers.forEach((coursier, index) => {
    const couleur = COULEURS[index % COULEURS.length];
    const chemin = coursier.tournee.chemin;

    if (coursier.tournee.depasse_heure_max) {
      const alerte = document.createElement('p');
      alerte.style.color = 'red';
      alerte.textContent = `Attention : le coursier ${coursier.nom} dépasse l'heure maximale.`;
      zone.appendChild(alerte);
    }

    // Légende : un carré de la couleur du coursier, suivi de son nom.
    const legende = document.createElement('p');
    legende.innerHTML =
      `<span style="color:${couleur}">&#9632;</span> ` +
      `Coursier ${coursier.nom} ${coursier.prenom} (${chemin.length} points)`;
    zone.appendChild(legende);

    // Le tracé : une polyligne qui relie tous les points du chemin, dans l'ordre.
    const points = chemin.map(p => [p.latitude, p.longitude]);
    coucheTournees.addLayer(L.polyline(points, { color: couleur, weight: 3 }));

    // Un marqueur sur chaque arrêt (pas sur les simples passages).
    for (const point of chemin) {
      if (point.type === 'passage') continue;

      const estEntrepot = point.type === 'entrepot';
      if (estEntrepot) {
        if (entrepotAffiche) continue;
        entrepotAffiche = true;
      }

      const marqueur = estEntrepot
        ? L.marker([point.latitude, point.longitude], { icon: iconeEntrepot })
        : L.marker([point.latitude, point.longitude]); // épingle par défaut

      marqueur.bindPopup(contenuPopup(point, coursier, estEntrepot));
      coucheTournees.addLayer(marqueur);
    }
  });
}

// Texte du popup d'un arrêt. Pas de coursier pour l'entrepôt (commun à tous).
function contenuPopup(point, coursier, estEntrepot) {
  const lignes = [`<b>${point.type.toUpperCase()}</b>`];
  if (!estEntrepot) lignes.push(`Coursier ${coursier.nom}`);
  if (point.livraison) lignes.push(`Livraison id #${point.livraison.id}`);
  lignes.push(`Latitude : ${point.latitude}`);
  lignes.push(`Longitude : ${point.longitude}`);
  lignes.push(`Adresse : ${point.adresse}`);

  let horaire = `Arrivée : ${formatTime(point.heure_arrivee)}`;
  if (point.heure_depart !== point.heure_arrivee) {
    horaire += ` — départ : ${formatTime(point.heure_depart)}`;
  }
  lignes.push(horaire);

  return lignes.join('<br>');
}
