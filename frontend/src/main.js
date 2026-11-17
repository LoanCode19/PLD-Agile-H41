import { displayJson } from './display.js';
import data from './sampleData.json';

document.querySelector('#app').innerHTML = `
  <button id="bouton">Afficher</button>
  <pre id="zone"></pre>
`;

const bouton = document.getElementById('bouton');
const zone = document.getElementById('zone');

// Au clic, on affiche le JSON (en dur pour l'instant)
bouton.addEventListener('click', () => {
  displayJson(data, zone);
});
