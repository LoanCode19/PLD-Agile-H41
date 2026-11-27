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

// Gris des points qu'aucun coursier ne prend en charge.
const GRIS = '#9e9e9e';

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

  const coursiers = (Array.isArray(data) ? data : [data])
    .filter(c => c?.tournee?.chemin?.length > 0);

  // La tournée d'un coursier est calculée quand on lui assigne des livraisons.
  if (coursiers.length === 0) {
    zone.textContent = 'Aucune tournée calculée : assignez des livraisons à un livreur.';
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

    // Le tracé, découpé en étapes (d'un arrêt au suivant), puis les flèches de direction.
    const etapeVers = dessinerEtapes(chemin, couleur, coucheTournees);
    ajouterFleches(chemin, couleur, coucheTournees);

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
      if (!estEntrepot) {
        relierPartenaireAuClic(marqueur, point, chemin, coucheTournees);
        surlignerEtapeAuClic(marqueur, etapeVers.get(point));
      }
      coucheTournees.addLayer(marqueur);
    }
  });
}

// Ajoute en gris les enlèvements et livraisons assignés à personne
// (réponse de GET /api/points-non-assignes : mêmes champs qu'un point de chemin,
// sans horaires). À appeler après displayTournees, qui vide la couche.
export function displayPointsNonAssignes(points, coucheTournees, zone) {
  if (points.length === 0) return;

  const legende = document.createElement('p');
  legende.innerHTML =
    `<span style="color:${GRIS}">&#9632;</span> ` +
    `Non assignées (${points.length / 2} livraison(s))`;
  zone.appendChild(legende);

  for (const point of points) {
    const marqueur = L.marker([point.latitude, point.longitude], {
      icon: iconeArret(point.type, GRIS, point.livraison.id),
    });
    marqueur.bindPopup(
      `<b>${point.type.toUpperCase()}</b><br>Non assignée<br>` +
      `Livraison ${point.livraison.id}<br>Adresse : ${point.adresse}`);
    // Même pointillé que pour les tournées : `points` contient la paire.
    relierPartenaireAuClic(marqueur, point, points, coucheTournees);
    coucheTournees.addLayer(marqueur);
  }
}

// Dessine le chemin en plusieurs polylignes : une par étape, d'un arrêt
// (entrepôt, enlèvement, livraison) jusqu'à l'arrêt suivant.
// Renvoie une Map : arrêt -> polyligne de l'étape qui arrive à cet arrêt.
function dessinerEtapes(chemin, couleur, coucheTournees) {
  const etapeVers = new Map();
  let morceau = [[chemin[0].latitude, chemin[0].longitude]];

  for (let i = 1; i < chemin.length; i++) {
    const point = chemin[i];
    morceau.push([point.latitude, point.longitude]);

    // Arrivée à un arrêt : l'étape est finie, la suivante repart d'ici.
    if (point.type !== 'passage') {
      const etape = L.polyline(morceau, { color: couleur, weight: 3 });
      coucheTournees.addLayer(etape);
      etapeVers.set(point, etape);
      morceau = [[point.latitude, point.longitude]];
    }
  }
  return etapeVers;
}

// Au clic sur un arrêt, épaissit l'étape qui y mène. Une étape va d'un arrêt
// au suivant sans retour en arrière : même si le tracé complet se croise,
// on voit sans ambiguïté par où passer.
function surlignerEtapeAuClic(marqueur, etape) {
  if (!etape) return;
  marqueur.on('popupopen', () => {
    etape.setStyle({ weight: 7 });
    etape.bringToFront(); // passe au-dessus des autres traits
  });
  marqueur.on('popupclose', () => etape.setStyle({ weight: 3 }));
}

// Pose une petite flèche au milieu d'un tronçon sur trois, tournée dans le sens
// de la marche : aux croisements, on voit quelles branches entrent et sortent.
function ajouterFleches(chemin, couleur, coucheTournees) {
  for (let i = 0; i < chemin.length - 1; i += 3) {
    const a = chemin[i];
    const b = chemin[i + 1];

    // Angle du tronçon (en degrés) : longitude = axe horizontal, latitude = axe vertical.
    const angle = Math.atan2(b.latitude - a.latitude, b.longitude - a.longitude) * 180 / Math.PI;

    // Triangle isocèle allongé (14 de long, 8 de large) pointant vers la droite
    // (l'est), puis tourné de -angle : en CSS, rotate() tourne dans le sens
    // horaire, alors que l'angle est anti-horaire.
    const fleche = L.divIcon({
      className: '',
      html: `<div style="transform:rotate(${-angle}deg)"><svg style="display:block" width="14" height="8" viewBox="0 0 14 8"><path d="M0 0L14 4L0 8z" fill="${couleur}" stroke="#fff" stroke-width="1"/></svg></div>`,
      iconSize: [14, 8],
      iconAnchor: [7, 4],
    });

    const milieu = [(a.latitude + b.latitude) / 2, (a.longitude + b.longitude) / 2];
    // interactive: false : la flèche ne bloque pas les clics ;
    // zIndexOffset négatif : elle passe sous les icônes des arrêts.
    coucheTournees.addLayer(L.marker(milieu, { icon: fleche, interactive: false, zIndexOffset: -1000 }));
  }
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
