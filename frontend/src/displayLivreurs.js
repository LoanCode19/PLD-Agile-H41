import './displayLivreurs.css';
import { API, appelerApi } from './api.js';

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
          <button id="annuler-livreurs" class="livreur-remove" type="button">Annuler</button>
        </div>
      </div>
      <p id="livreur-message" class="livreur-message" role="status"></p>

      <div class="livreur-actions livreur-add-actions">
        <button id="afficher-livreurs" class="livreur-primary" type="button">Afficher les livreurs</button>
        <button id="ouvrir-livreurs" class="livreur-primary" type="button">Ajouter</button>
      </div>
    </section>
  `;

  const afficherBouton = zone.querySelector('#afficher-livreurs');
  const ouvrirLivreurs = zone.querySelector('#ouvrir-livreurs');
  const formulaireLivreurs = zone.querySelector('#livreur-formulaire');
  const livreurList = zone.querySelector('#livreur-list');
  const validerLivreurs = zone.querySelector('#valider-livreurs');
  const annulerLivreurs = zone.querySelector('#annuler-livreurs');
  const livreurMessage = zone.querySelector('#livreur-message');
  const livreurTable = zone.querySelector('#livreur-table');

  // Derniers coursiers reçus du backend ({ id, prenom, nom, ... }).
  let coursiersConnus = [];

  function afficherMessage(message, type = '') {
    livreurMessage.textContent = message;
    livreurMessage.className = `livreur-message ${type}`.trim();
  }

  // Un champ texte avec son libellé ; `name` sert à le retrouver à la validation.
  function creerChamp(libelle, name, placeholder) {
    const label = document.createElement('label');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = name;
    input.placeholder = placeholder;
    label.append(document.createTextNode(libelle), input);
    return label;
  }

  function actualiserNumeros() {
    const cards = [...livreurList.querySelectorAll('.livreur-card')];
    cards.forEach((card, index) => {
      card.querySelector('.livreur-card-titre').textContent = `Nouveau livreur ${index + 1}`;
      card.querySelector('.livreur-remove').hidden = cards.length === 1;
    });
  }

  function ajouterBlocLivreur() {
    const card = document.createElement('div');
    card.className = 'livreur-card';

    const titre = document.createElement('strong');
    titre.className = 'livreur-card-titre';

    const champs = document.createElement('div');
    champs.className = 'livreur-champs';
    const champPrenom = creerChamp('Prénom', 'prenom', 'Exemple : Marie');
    champs.append(champPrenom, creerChamp('Nom', 'nom', 'Exemple : Dupont'));

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'livreur-remove';
    remove.textContent = 'Retirer';
    remove.addEventListener('click', () => {
      card.remove();
      actualiserNumeros();
    });

    card.append(titre, champs, remove);
    livreurList.insertBefore(card, livreurList.querySelector('.livreur-add-card'));
    actualiserNumeros();
    champPrenom.querySelector('input').focus();
  }

  function ajouterBoutonAutreLivreur() {
    const addCard = document.createElement('button');
    addCard.type = 'button';
    addCard.className = 'livreur-add-card';
    addCard.textContent = 'Ajouter un autre livreur';
    addCard.addEventListener('click', ajouterBlocLivreur);
    livreurList.appendChild(addCard);
  }

  function fermerFormulaire() {
    livreurList.replaceChildren();
    formulaireLivreurs.hidden = true;
    ouvrirLivreurs.hidden = false;
  }

  function afficherTable() {
    livreurTable.replaceChildren();
    if (coursiersConnus.length === 0) {
      livreurTable.textContent = 'Aucun livreur.';
      return;
    }
    coursiersConnus.forEach(coursier => {
      const row = document.createElement('div');
      row.className = 'livreur-row';

      const id = document.createElement('strong');
      id.textContent = String(coursier.id).padStart(4, '0');

      const name = document.createElement('span');
      const nomComplet = `${coursier.prenom} ${coursier.nom}`.trim();
      name.textContent = nomComplet || '(sans nom)';

      row.append(id, name);
      livreurTable.appendChild(row);
    });
  }

  // Récupère la liste des coursiers du backend et l'affiche.
  // Renvoie false si la requête a échoué (le message d'erreur est affiché).
  async function chargerCoursiers() {
    try {
      coursiersConnus = await appelerApi(`${API}/coursiers`);
      afficherTable();
      return true;
    } catch (error) {
      afficherMessage(error.message, 'error');
      return false;
    }
  }

  afficherBouton.addEventListener('click', async () => {
    afficherMessage('');
    await chargerCoursiers();
  });

  ouvrirLivreurs.addEventListener('click', () => {
    formulaireLivreurs.hidden = false;
    ouvrirLivreurs.hidden = true;
    afficherMessage('');

    livreurList.replaceChildren();
    ajouterBoutonAutreLivreur();
    ajouterBlocLivreur();
  });

  annulerLivreurs.addEventListener('click', () => {
    fermerFormulaire();
    afficherMessage('');
  });

  validerLivreurs.addEventListener('click', async () => {
    const cards = [...livreurList.querySelectorAll('.livreur-card')];
    const nouveaux = cards.map(card => ({
      prenom: card.querySelector('input[name="prenom"]').value.trim(),
      nom: card.querySelector('input[name="nom"]').value.trim()
    }));

    // Chaque livreur doit avoir un prénom et un nom.
    const vide = cards
      .flatMap(card => [...card.querySelectorAll('input')])
      .find(input => input.value.trim() === '');
    if (vide) {
      afficherMessage('Veuillez renseigner le prénom et le nom de chaque livreur.', 'error');
      vide.focus();
      return;
    }

    // Pas deux fois la même personne (sans tenir compte des majuscules),
    // ni entre les nouveaux, ni avec les livreurs déjà connus.
    const cle = c => `${c.prenom} ${c.nom}`.trim().toLowerCase();
    const tous = [...coursiersConnus, ...nouveaux].map(cle);
    if (new Set(tous).size !== tous.length) {
      afficherMessage('Deux livreurs ne peuvent pas avoir le même prénom et nom.', 'error');
      return;
    }

    validerLivreurs.disabled = true;
    afficherMessage('Envoi en cours…');

    try {
      // Pas d'id : c'est le backend qui l'attribue.
      await appelerApi(`${API}/add-coursiers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nouveaux)
      });

      fermerFormulaire();
      // On relit la liste du backend pour afficher les ids qu'il a attribués.
      if (await chargerCoursiers()) {
        afficherMessage(`${nouveaux.length} livreur(s) ajouté(s).`, 'success');
      }
    } catch (error) {
      afficherMessage(error.message, 'error');
    } finally {
      validerLivreurs.disabled = false;
    }
  });
}
