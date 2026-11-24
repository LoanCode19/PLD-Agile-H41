import L from 'leaflet';
import { formatTime } from './displayLivraisons.js';

// Les images de l'icône par défaut (l'épingle) doivent être importées
// explicitement : Leaflet les cherche normalement par URL relative, ce qui
// ne marche pas une fois le code bundlé par Vite.
import iconeEpingle from 'leaflet/dist/images/marker-icon.png';
import iconeEpingle2x from 'leaflet/dist/images/marker-icon-2x.png';
import ombreEpingle from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: iconeEpingle,
  iconRetinaUrl: iconeEpingle2x,
  shadowUrl: ombreEpingle,
});

// Marqueur personnalisé pour l'entrepot, bien différentiable des épingles.
const iconeEntrepot = L.divIcon({
  className: 'icone-entrepot',
  html: '<div style="width:26px;height:26px;background:#1a1a2e;color:#fff;border:2px solid #fff;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:bold;box-shadow:0 0 6px rgba(0,0,0,.5);">E</div>',
  iconSize: [26, 26],
  iconAnchor: [13, 13],
  popupAnchor: [0, -14],
});

// Une couleur par coursier, on repart au début si on dépasse la liste.
const COULEURS = ['#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#008080', '#9a6324', '#800000'];

// Un marqueur n'est posé que sur ces types de point du chemin.
const TYPES_MARQUEURS = ['entrepot', 'livraison', 'enlevement'];

// L'API renvoie les heures en secondes (nombre) ; par sécurité on accepte
// aussi une chaîne déjà formatée "HH:MM:SS".
function formaterHeure(heure) {
  if (typeof heure === 'number') return formatTime(heure);
  return heure === undefined || heure === null ? '' : String(heure);
}

// Dessine la tournée du (ou des) coursier(s) sur la carte.
// L'API renvoie un objet Coursier :
// {
//   "id": ..., "nom": ..., "prenom": ...,
//   "livraisons": [ { id, adresse_enlevement, adresse_livraison, ... } ],
//   "tournee": {
//     "chemin": [ { adresse, latitude, longitude, type, livraison, heure_arrivee, heure_depart } ],
//     "depasse_heure_max": true/false
//   }
// }
// Un tableau de coursiers est aussi accepté, pour quand l'API en renverra
// plusieurs.
export function displayTournees(data, coucheTournees, zone) {
  coucheTournees.clearLayers();
  zone.replaceChildren();

  // 1) Vérifications : erreur renvoyée par l'API ({detail: "..."}) ou
  //    réponse inattendue.
  if (!data || data.detail) {
    zone.textContent = `Erreur : ${data?.detail ?? 'aucune réponse de l\u2019API'}`;
    return;
  }

  const coursiers = Array.isArray(data) ? data : [data];
  const coursiersAvecTournee = coursiers.filter(c => c?.tournee?.chemin?.length > 0);

  if (coursiersAvecTournee.length === 0) {
    zone.textContent = 'Aucune tournée calculée.';
    return;
  }

  // 2) L'entrepot est commun à tous : son marqueur ne sera posé qu'une
  //    fois, au premier "entrepot" lu.
  let entrepotAffiche = false;

  coursiersAvecTournee.forEach((coursier, index) => {
    const couleur = COULEURS[index % COULEURS.length];
    const chemin = coursier.tournee.chemin;

    // 3) Alerte en rouge si l'heure maximale est dépassée.
    if (coursier.tournee.depasse_heure_max) {
      const alerte = document.createElement('p');
      alerte.style.color = 'red';
      alerte.textContent =
        `Attention : le coursier ${coursier.nom} dépasse l'heure maximale.`;
      zone.appendChild(alerte);
    }

    // 4) Légende : un carré de la couleur du coursier, avec son nom.
    const legend = document.createElement('p');
    legend.innerHTML =
      `<span style="color:${couleur}">&#9632;</span> ` +
      `Coursier ${coursier.nom} ${coursier.prenom} (${chemin.length} points)`;
    zone.appendChild(legend);

    // 5) Le tracé : array de coordonnées au format Leaflet [lat, lng],
    //    dans l'ordre du chemin, reliées par une polyligne.
    const points = chemin.map(point => [point.latitude, point.longitude]);
    coucheTournees.addLayer(L.polyline(points, { color: couleur, weight: 3 }));

    // 6) Marqueurs sur les points d'intérêt uniquement : une épingle
    //    standard pour livraison / enlèvement, le marqueur "E" pour l'entrepot.
    chemin.forEach(point => {
      const type = (point.type ?? '').toLowerCase();
      if (!TYPES_MARQUEURS.includes(type)) return;

      const isEntrepot = type === 'entrepot';
      if (isEntrepot && entrepotAffiche) return;
      if (isEntrepot) entrepotAffiche = true;

      // Sans option icon, L.marker utilise l'épingle par défaut (l'icône
      // par défaut qu'on a recâblée plus haut).
      const coords = [point.latitude, point.longitude];
      const marker = isEntrepot
        ? L.marker(coords, { icon: iconeEntrepot })
        : L.marker(coords);

      // L'entrepot étant commun à tous les coursiers, on n'indique pas de
      // coursier dans son popup. Si le point est lié à une livraison, on
      // affiche son id pour pouvoir la retrouver dans la liste.
      const livre = point.livraison?.id;
      marker.bindPopup(
        `<b>${type.toUpperCase()}</b><br>` +
        (isEntrepot ? '' : `Coursier ${coursier.nom}<br>`) +
        (livre !== undefined ? `Livraison #${livre}<br>` : '') +
        `Latitude : ${point.latitude}<br>` +
        `Longitude : ${point.longitude}<br>` +
        `Adresse : ${point.adresse}<br>` +
        `Arrivée : ${formaterHeure(point.heure_arrivee)}` +
        (point.heure_depart !== point.heure_arrivee
          ? ` — départ : ${formaterHeure(point.heure_depart)}`
          : '')
      );
      coucheTournees.addLayer(marker);
    });
  });
}
