function formatTime(seconds) {
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
  zone.innerHTML = '';

  if (data.detail) {
    zone.textContent = `Erreur : ${data.detail}`;
    return;
  }

  const summary = document.createElement('p');

  summary.textContent =
    `Entrepôt : ${data.adresse_entrepot} | ` +
    `Départ : ${formatTime(data.heure_depart)} | ` +
    `${data.livraisons.length} livraison(s)`;

  zone.appendChild(summary);

  const list = document.createElement('ul');

  data.livraisons.forEach((livraison, index) => {
    const item = document.createElement('li');

    item.textContent =
      `Livraison ${index + 1} — ` +
      `Enlèvement : ${livraison.adresse_enlevement} ` +
      `(${formatDuration(livraison.duree_enlevement)}) — ` +
      `Livraison : ${livraison.adresse_livraison} ` +
      `(${formatDuration(livraison.duree_livraison)})`;

    list.appendChild(item);
  });

  zone.appendChild(list);
}