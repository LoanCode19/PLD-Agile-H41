import L from 'leaflet';
import { formatTime } from './displayLivraisons.js';

// Icônes issues de Tabler Icons (https://tabler.io/icons, licence MIT) :
// "package-export" pour l'enlèvement, "package-import" pour la livraison,
// "building-warehouse" pour l'entrepôt.
// Les deux icônes de colis dessinent le même colis, seule la flèche change.
const SVG_COLIS =
  '<path d="M12 21l-8 -4.5v-9l8 -4.5l8 4.5v4.5" />' +
  '<path d="M12 12l8 -4.5" /><path d="M12 12v9" /><path d="M12 12l-8 -4.5" />';
const ENLEVEMENT = '<path d="M15 18h7" /><path d="M19 15l3 3l-3 3" />'; // flèche sortante
const LIVRAISON = '<path d="M22 18h-7" /><path d="M18 15l-3 3l3 3" />';  // flèche entrante
const SVG_ENTREPOT =
  '<path d="M3 21v-13l9 -4l9 4v13" /><path d="M13 13h4v8h-10v-6h6" />' +
  '<path d="M13 21v-9a1 1 0 0 0 -1 -1h-2a1 1 0 0 0 -1 1v3" />';

// Renvoie le <svg> de l'icône selon le type du point :
// "enlevement", "livraison", sinon l'entrepôt.
// stroke="currentColor" : le trait prend la couleur CSS du parent.
function svgIcone(type) {
  let traces;
  if (type === 'enlevement') traces = SVG_COLIS + ENLEVEMENT;
  else if (type === 'livraison') traces = SVG_COLIS + LIVRAISON;
  else traces = SVG_ENTREPOT;

  return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
    traces + '</svg>';
}

// Marqueur d'un enlèvement ou d'une livraison : l'icône de colis dans un rond
// blanc bordé de la couleur du coursier (le fond blanc la rend lisible sur la carte).
// Une pastille en haut à droite affiche le numéro de la livraison :
// l'enlèvement et la livraison d'une même paire ont le même numéro.
function iconeArret(type, couleur, numero) {
  const pastille = `<span style="position:absolute;top:-8px;right:-10px;min-width:16px;padding:0 3px;background:${couleur};color:#fff;border-radius:8px;font-size:11px;font-weight:bold;line-height:16px;text-align:center;">${numero}</span>`;
  return L.divIcon({
    className: '', // sinon Leaflet ajoute un carré blanc par défaut
    html: `<div style="position:relative;width:28px;height:28px;background:#fff;color:${couleur};border:2px solid ${couleur};border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 4px rgba(0,0,0,.4);">${svgIcone(type)}${pastille}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
}

// Marqueur de l'entrepôt : carré au fond sombre et icône blanche, l'inverse
// des arrêts (rond blanc, icône colorée) pour qu'il ressorte sur la carte.
// Le bleu nuit ne fait pas partie des couleurs des coursiers.
const iconeEntrepot = L.divIcon({
  className: '',
  html: `<div style="width:30px;height:30px;background:#1a1a2e;color:#fff;border:2px solid #fff;border-radius:6px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 6px rgba(0,0,0,.5);">${svgIcone('entrepot')}</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
  popupAnchor: [0, -16],
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

      const icone = estEntrepot ? iconeEntrepot : iconeArret(point.type, couleur, point.livraison.id);
      const marqueur = L.marker([point.latitude, point.longitude], { icon: icone });

      marqueur.bindPopup(contenuPopup(point, coursier, estEntrepot));
      if (!estEntrepot) relierPartenaireAuClic(marqueur, point, chemin, coucheTournees);
      coucheTournees.addLayer(marqueur);
    }
  });
}

// Au clic sur un enlèvement (ou une livraison), trace un trait en pointillés
// jusqu'à l'autre point de la même paire. Le trait disparaît quand le popup se ferme.
// Leaflet n'ouvre qu'un popup à la fois, donc un seul trait est visible à la fois.
function relierPartenaireAuClic(marqueur, point, chemin, coucheTournees) {
  // Le partenaire : même livraison, mais l'autre type (enlèvement <-> livraison).
  // (les simples passages n'ont pas de livraison, ils ne sont donc jamais trouvés)
  const partenaire = chemin.find(p =>
    p.livraison?.id === point.livraison.id && p.type !== point.type);
  if (!partenaire) return;

  const trait = L.polyline(
    [[point.latitude, point.longitude], [partenaire.latitude, partenaire.longitude]],
    { color: "black", weight: 3, dashArray: '8 8' },
  );

  marqueur.on('popupopen', () => coucheTournees.addLayer(trait));
  marqueur.on('popupclose', () => coucheTournees.removeLayer(trait));
}

// Texte du popup d'un arrêt. Pas de coursier pour l'entrepôt (commun à tous).
function contenuPopup(point, coursier, estEntrepot) {
  const lignes = [`<b>${point.type.toUpperCase()}</b>`];
  if (!estEntrepot) lignes.push(`Coursier ${coursier.nom}`);
  if (point.livraison) lignes.push(`Livraison ${point.livraison.id}`);
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
