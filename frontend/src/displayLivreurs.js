import './displayLivreurs.css';

export function setupLivreurs(zone) {
  zone.innerHTML = `
    <section class="livreur-section">
      <div class="livreur-header">
        <h2>Liste des livreurs</h2>
      </div>

      <div id="livreur-table" class="livreur-table"></div>

      <div id="livreur-formulaire" hidden>
        <div id="livreur-list" class="livreur-list"></div>
        <div class="livreur-actions">
          <button id="valider-livreurs" class="livreur-primary" type="button">Valider</button>
        </div>
        <p id="livreur-message" class="livreur-message" role="status"></p>
      </div>

      <div class="livreur-actions livreur-add-actions">
        <button id="ouvrir-livreurs" class="livreur-primary" type="button">Ajouter</button>
      </div>
    </section>
  `;

  const ouvrirLivreurs = zone.querySelector('#ouvrir-livreurs');
  const formulaireLivreurs = zone.querySelector('#livreur-formulaire');
  const livreurList = zone.querySelector('#livreur-list');
  const validerLivreurs = zone.querySelector('#valider-livreurs');
  const livreurMessage = zone.querySelector('#livreur-message');
  const livreurTable = zone.querySelector('#livreur-table');
  const livreursValides = [];

  function afficherMessage(message, type = '') {
    livreurMessage.textContent = message;
    livreurMessage.className = `livreur-message ${type}`.trim();
  }

  function actualiserNumeros() {
    const cards = [...livreurList.querySelectorAll('.livreur-card')];
    const baseIndex = livreursValides.length;

    cards.forEach((card, index) => {
      const input = card.querySelector('input');
      const label = card.querySelector('label');

      input.id = `livreur-${baseIndex + index}`;
      label.htmlFor = input.id;
      label.firstChild.textContent = `Nom du livreur ${baseIndex + index + 1}`;

      card.querySelector('.livreur-remove').hidden = cards.length === 1;
    });
  }

  function ajouterBlocLivreur() {
    const card = document.createElement('div');
    card.className = 'livreur-card';

    const label = document.createElement('label');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'livreur';
    input.placeholder = 'Exemple : Marie Dupont';

    label.appendChild(document.createTextNode('Nom du livreur'));
    label.appendChild(input);

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'livreur-remove';
    remove.textContent = 'Retirer';
    remove.addEventListener('click', () => {
      card.remove();
      actualiserNumeros();
    });

    card.append(label, remove);
    livreurList.insertBefore(card, livreurList.querySelector('.livreur-add-card'));
    actualiserNumeros();
    input.focus();
  }

  function mettreAJourBoutonAjouter() {
    if (!livreurList.querySelector('.livreur-add-card')) {
      const addCard = document.createElement('button');
      addCard.type = 'button';
      addCard.className = 'livreur-add-card';
      addCard.textContent = 'Ajouter un autre livreur';
      addCard.addEventListener('click', ajouterBlocLivreur);
      livreurList.appendChild(addCard);
    }
  }

  function afficherLivreurs() {
    livreurTable.replaceChildren();

    livreursValides.forEach((nom, index) => {
      const row = document.createElement('div');
      row.className = 'livreur-row';

      const id = document.createElement('strong');
      id.textContent = String(index + 1).padStart(4, '0');

      const name = document.createElement('span');
      name.textContent = nom;

      row.append(id, name);
      livreurTable.appendChild(row);
    });
  }

  ouvrirLivreurs.addEventListener('click', () => {
    formulaireLivreurs.hidden = false;
    ouvrirLivreurs.hidden = true;

    livreurList.replaceChildren();
    mettreAJourBoutonAjouter();
    ajouterBlocLivreur();
  });

  validerLivreurs.addEventListener('click', async () => {
    const inputs = [...livreurList.querySelectorAll('input[name="livreur"]')];
    const noms = inputs.map(input => input.value.trim()).filter(Boolean);

    if (noms.length !== inputs.length) {
      afficherMessage('Veuillez renseigner le nom de chaque livreur.', 'error');
      const vide = inputs.find(input => input.value.trim() === '');
      if (vide) vide.focus();
      return;
    }

    const nomsNormalises = noms.map(nom => nom.toLowerCase());
    const tousLesNoms = [...livreursValides, ...noms].map(nom => nom.toLowerCase());

    if (
      new Set(nomsNormalises).size !== nomsNormalises.length ||
      tousLesNoms.some((nom, index) => tousLesNoms.indexOf(nom) !== index)
    ) {
      afficherMessage('Deux livreurs ne peuvent pas avoir le même nom.', 'error');
      return;
    }

    livreursValides.push(...noms);
    afficherLivreurs();

    livreurList.replaceChildren();
    formulaireLivreurs.hidden = true;
    ouvrirLivreurs.hidden = false;

    validerLivreurs.disabled = true;
    afficherMessage('Envoi en cours…');

    try {
      const response = await fetch('http://localhost:8080/api/livreurs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ livreurs: livreursValides })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Impossible d’envoyer la liste des livreurs');
      }

      afficherMessage(`${livreursValides.length} livreur(s) enregistré(s).`, 'success');
    } catch (error) {
      afficherMessage(error.message, 'error');
    } finally {
      validerLivreurs.disabled = false;
    }
  });
}
