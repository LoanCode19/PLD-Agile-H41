// Affiche le JSON brut, indenté de 2 espaces, dans la zone.
export function displayJson(json, zone) {
  zone.textContent = JSON.stringify(json, null, 2);
}
