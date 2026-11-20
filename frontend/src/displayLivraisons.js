
export function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return remainingSeconds === 0
    ? `${minutes} min`
    : `${minutes} min ${remainingSeconds} s`;
}

export function displayLivraisons(data, zone) {
  zone.replaceChildren();

  // Display backend parsing errors
  if (data.detail) {
    const error = document.createElement('p');
    error.textContent = `Erreur : ${data.detail}`;
    zone.appendChild(error);
    return;
  }

  if (!Array.isArray(data.livraisons)) {
    zone.textContent = 'Format de données invalide';
    return;
  }

  const summary = document.createElement('p');
  summary.textContent =
    `Entrepôt : ${data.adresseEntrepot} | ` +
    `Départ : ${formatTime(data.heureDepart)} | ` +
    `${data.livraisons.length} livraison(s)`;

  zone.appendChild(summary);

  const list = document.createElement('ul');

  data.livraisons.forEach(livraison => {
    const item = document.createElement('li');

    item.textContent =
      `Livraison ${livraison.id} — ` +
      `Enlèvement : ${livraison.adresseEnlevement} ` +
      `(${formatDuration(livraison.dureeEnlevement)}) — ` +
      `Livraison : ${livraison.adresseLivraison} ` +
      `(${formatDuration(livraison.dureeLivraison)})`;

    list.appendChild(item);
  });

  zone.appendChild(list);
}
