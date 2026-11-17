import { displayJson } from './display.js';

document.querySelector('#app').innerHTML = `
  <button id="bouton">Afficher</button>
  <pre id="zone"></pre>
`;

const bouton = document.getElementById('bouton');
const zone = document.getElementById('zone');

// Au clic, on affiche le JSON (en dur pour l'instant)
bouton.addEventListener('click', () => {
    fetch('http://localhost:8000/api/route-graph')
        .then(response => response.json())
        .then(data => displayJson(data, zone));
});
