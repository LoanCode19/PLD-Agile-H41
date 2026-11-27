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

export function displayLivraisons(data, zone) {
  // Les erreurs sont traitées avant (appelerApi) : `data` est toujours valide.
  zone.innerHTML = '';

  const summary = document.createElement('p');

  summary.textContent =
    `Entrepôt : ${data.adresse_entrepot} | ` +
    `Départ : ${formatTime(data.heure_depart)} | ` +
    `${data.livraisons.length} livraison(s)`;

  zone.appendChild(summary);

  const list = document.createElement('ul');

  data.livraisons.forEach(livraison => {
    const item = document.createElement('li');

    // On affiche l'id donné par l'API (et non la position dans la liste) :
    // c'est le même numéro que celui affiché sur la carte.
    item.textContent =
      `Livraison ${livraison.id} — ` +
      `Enlèvement : ${livraison.adresse_enlevement} ` +
      `(${formatDuration(livraison.duree_enlevement)}) — ` +
      `Livraison : ${livraison.adresse_livraison} ` +
      `(${formatDuration(livraison.duree_livraison)})`;

    list.appendChild(item);
  });

  zone.appendChild(list);
}