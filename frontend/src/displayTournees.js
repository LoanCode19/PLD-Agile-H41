import L from 'leaflet';

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

// Dessine les tournées sur la carte : une polyligne par coursier, un
// marqueur sur les passages ENTREPOT / LIVRAISON / ENLEVEMENT.
// data a cette forme :
// {
//   "demandeDeTournees": {
//     "coursiers": [
//       { "id": "...", "nom": "...", "passages": [ { latitude, longitude, adresse, type, heure_arrivee, heure_depart }, ... ] }
//     ]
//   }
// }
export function displayTournees(data, coucheTournees, zone) {
  coucheTournees.clearLayers();
  zone.replaceChildren();

  // 1) On descend dans le JSON jusqu'à la liste des coursiers, et on
  //    vérifie qu'on a bien ce qu'on attend.
  const coursiers = data?.demandeDeTournees?.coursiers;

  if (!Array.isArray(coursiers)) {
    const error = document.createElement('p');
    error.textContent = data?.detail
      ? `Erreur : ${data.detail}`
      : 'Format de données invalide (demandeDeTournees.coursiers attendu)';
    zone.appendChild(error);
    return;
  }

  if (coursiers.length === 0) {
    zone.textContent = 'Aucune tournée calculée.';
    return;
  }

  // 2) Une couleur par coursier, et une légende pour les reconnaître.
  // L'entrepot est commun à tous : on n'affiche son marqueur qu'une fois,
  // au premier ENTREPOT lu.
  let entrepotAffiche = false;

  coursiers.forEach((coursier, index) => {
    const couleur = COULEURS[index % COULEURS.length];

    const legend = document.createElement('p');
    legend.innerHTML =
      `<span style="color:${couleur}">&#9632;</span> ` +
      `Coursier ${coursier.nom} (${coursier.passages.length} passages)`;
    zone.appendChild(legend);

    // 3) Le tracé : array de coordonnées au format Leaflet [lat, lng],
    //    dans l'ordre des passages, reliées par une polyligne.
    const points = coursier.passages.map(passage => [passage.latitude, passage.longitude]);
    coucheTournees.addLayer(L.polyline(points, { color: couleur, weight: 3 }));

    // 4) Marqueurs sur les points d'intérêt uniquement : une épingle
    //    standard pour livraison / enlèvement, le marqueur "E" pour l'entrepot.
    coursier.passages.forEach(passage => {
      if (!['ENTREPOT', 'LIVRAISON', 'ENLEVEMENT'].includes(passage.type)) return;

      const isEntrepot = passage.type === 'ENTREPOT';
      // L'entrepot est commun à tous : une seule fois, au premier lu.
      if (isEntrepot && entrepotAffiche) return;
      if (isEntrepot) entrepotAffiche = true;

      // Sans option icon, L.marker utilise l'épingle par défaut (l'icône
      // par défaut qu'on a recâblée plus haut).
      const coords = [passage.latitude, passage.longitude];
      const marker = isEntrepot
        ? L.marker(coords, { icon: iconeEntrepot })
        : L.marker(coords);

      // L'entrepot étant partagé par tous les coursiers, on n'indique
      // pas de coursier dans son popup. On affiche les coordonnées partout.
      marker.bindPopup(
        `<b>${passage.type}</b><br>` +
        (isEntrepot ? '' : `Coursier ${coursier.nom}<br>`) +
        `Latitude : ${passage.latitude}<br>` +
        `Longitude : ${passage.longitude}<br>` +
        `Adresse : ${passage.adresse}<br>` +
        `Arrivée : ${passage.heure_arrivee}` +
        (passage.heure_depart !== passage.heure_arrivee ? ` — départ : ${passage.heure_depart}` : '')
      );
      coucheTournees.addLayer(marker);
    });
  });
}
