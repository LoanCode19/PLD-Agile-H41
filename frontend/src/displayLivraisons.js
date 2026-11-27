export function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

function formatDuration(seconds) {
  if (seconds === 0) {
    return '0 min';
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (remainingSeconds === 0) {
    return `${minutes} min`;
  }

  return `${minutes} min ${remainingSeconds} s`;
}

// Nom affiché d'un coursier dans les listes déroulantes.
function nomCoursier(coursier) {
  const nom = `${coursier.prenom} ${coursier.nom}`.trim();
  return nom || `Coursier ${coursier.id}`;
}

// Choix faits dans les listes déroulantes : Map idLivraison -> idCoursier
// (les livraisons « Non assignée » n'y sont pas).
function choixActuels(zone) {
  const choix = new Map();
  zone.querySelectorAll('select[data-livraison]').forEach(select => {
    if (select.value) choix.set(Number(select.dataset.livraison), Number(select.value));
  });
  return choix;
}

// Assignations à envoyer au backend : Map idCoursier -> [ids des livraisons].
export function lireAssignations(zone) {
  const parCoursier = new Map();
  for (const [idLivraison, idCoursier] of choixActuels(zone)) {
    if (!parCoursier.has(idCoursier)) parCoursier.set(idCoursier, []);
    parCoursier.get(idCoursier).push(idLivraison);
  }
  return parCoursier;
}

// Affiche la demande, avec pour chaque livraison une liste déroulante pour
// choisir son coursier. `coursiers` vient de GET /api/coursiers.
// Si les listes sont déjà affichées (ex. on vient d'ajouter un livreur), les
// choix en cours sont conservés ; sinon on présélectionne le coursier auquel
// le backend a déjà assigné la livraison.
export function displayLivraisons(data, coursiers, zone) {
  // Les erreurs sont traitées avant (appelerApi) : `data` est toujours valide.
  const choixEnCours = choixActuels(zone);
  zone.innerHTML = '';

  // idLivraison -> idCoursier, d'après le backend.
  const assigneeA = new Map();
  for (const coursier of coursiers) {
    for (const livraison of coursier.livraisons) assigneeA.set(livraison.id, coursier.id);
  }

  const summary = document.createElement('p');

  summary.textContent =
    `Entrepôt : ${data.adresse_entrepot} | ` +
    `Départ : ${formatTime(data.heure_depart)} | ` +
    `${data.livraisons.length} livraison(s)`;

  zone.appendChild(summary);

  if (coursiers.length === 0) {
    const aide = document.createElement('p');
    aide.style.color = '#b91c1c';
    aide.textContent = 'Aucun livreur : ajoutez des livreurs pour pouvoir assigner les livraisons.';
    zone.appendChild(aide);
  }

  const list = document.createElement('ul');

  data.livraisons.forEach(livraison => {
    const item = document.createElement('li');

    // On affiche l'id donné par l'API (et non la position dans la liste) :
    // c'est le même numéro que celui affiché sur la carte.
    const texte = document.createElement('span');
    texte.textContent =
      `Livraison ${livraison.id} — ` +
      `Enlèvement : ${livraison.adresse_enlevement} ` +
      `(${formatDuration(livraison.duree_enlevement)}) — ` +
      `Livraison : ${livraison.adresse_livraison} ` +
      `(${formatDuration(livraison.duree_livraison)}) — `;

    const select = document.createElement('select');
    select.dataset.livraison = livraison.id;
    select.add(new Option('Non assignée', ''));
    for (const coursier of coursiers) {
      select.add(new Option(nomCoursier(coursier), coursier.id));
    }
    const choisi = choixEnCours.has(livraison.id)
      ? choixEnCours.get(livraison.id)
      : assigneeA.get(livraison.id);
    // Un coursier qui n'existe plus (ex. nouvelle carte) retombe sur « Non assignée ».
    select.value = coursiers.some(c => c.id === choisi) ? String(choisi) : '';

    item.append(texte, select);
    list.appendChild(item);
  });

  zone.appendChild(list);
}