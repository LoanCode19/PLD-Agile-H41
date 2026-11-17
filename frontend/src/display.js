// Affiche le contenu du JSON dans la zone, ligne par ligne.
// Le JSON est un objet : pour chaque clé, on affiche son nom, puis ses éléments un par ligne.
export function displayJson(json, zone) {
  let texte = "";

  for (const cle in json) {
    texte = texte + cle + "\n";

    for (const element of json[cle]) {
      texte = texte + JSON.stringify(element) + "\n";
    }
  }

  zone.textContent = texte;
}
