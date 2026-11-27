# PLD Agile - H41

## Démarrage rapide

### Prérequis

- **Python >= 3.11** (le code utilise `enum.StrEnum`)
- **Node.js >= 20** et `npm` (pour Vite 8)

### 1. Installer les dépendances (une seule fois)

Backend — toutes les dépendances Python sont dans `backend/requirements.txt` (`fastapi`, `uvicorn`, `python-multipart` pour l'upload de fichiers, `pytest` et `httpx` pour les tests) :

```bash
cd backend
python -m venv .venv

# Activer l'environnement virtuel
.venv\Scripts\activate          # Windows (PowerShell / cmd)
source .venv/bin/activate        # macOS / Linux

pip install -r requirements.txt
```

Frontend — les dépendances (`vite`, `leaflet`) sont dans `frontend/package.json` :

```bash
cd frontend
npm install
```

### 2. Lancer les serveurs

Ouvrir deux terminaux (avec le venv activé pour le backend) :

```bash
# terminal 1 — backend (API sur http://localhost:8080)
cd backend
python -m uvicorn api:app --reload --port 8080

# terminal 2 — frontend
cd frontend
npm run dev        # puis ouvrir http://localhost:5173 dans le navigateur
```

### 3. Utiliser l'application

Au démarrage, aucune donnée n'est chargée : tout part des fichiers XML que vous uploadez (exemples dans `ressources/`).

1. **Uploader une carte** (ex. `petitPlan.xml`).
2. **Uploader les livraisons** de cette carte (ex. `demandePetit1.xml`) : elles s'affichent en bas de la page.
3. **Afficher les tournées** : la tournée est calculée sur la carte et les livraisons uploadées.

Les boutons ne s'activent que dans cet ordre. Uploader une nouvelle carte efface les livraisons : il faut les ré-uploader.

### 4. Lancer les tests

```bash
cd backend
python -m pytest
```

---

Guide des bonnes pratiques à respecter sur ce dépôt.

## Structure du dépôt

| Dossier     | Contenu                                                                 |
|-------------|-------------------------------------------------------------------------|
| `frontend/` | Tout le code du front (interface, composants, appels à l'API...)        |
| `backend/`  | Tout le code du back (API, logique métier, accès aux données...)        |
| `docs/`     | Toute la documentation : diagrammes de classes, de séquence, maquettes, comptes rendus, etc. |
| `ressources/` | Données et fichiers à aller chercher : liste des livraisons à effectuer, coordonnées des intersections, et toutes les ressources graphiques (images, icônes, cartes...) |

Ne pas mélanger : pas de code front dans `backend/`, pas de doc dans `frontend/`, etc.

Le dossier `ressources/` ne contient **pas de code** : seulement des fichiers de données ou graphiques, lus par le front et/ou le back. Si un fichier change de nom, de format ou de structure, le signaler dans la PR et mettre à jour la documentation des formats (voir plus bas), car front et back en dépendent.

## Workflow Git

1. **Une branche par feature / fix.** On ne travaille jamais directement sur `main`.
2. **Nommage des branches** : `type/description-courte`
   - `feature/creation-livraison`
   - `fix/erreur-calcul-trajet`
   - `docs/diagramme-classes`
3. **Commits** : petits, fréquents, avec un message clair à l'impératif (ex. `Ajoute la validation du formulaire`).
4. **Pull Request obligatoire** pour merger dans `main` :
   - titre explicite + courte description de ce qui a été fait ;
   - au moins **1 relecture** d'un autre membre de l'équipe avant merge ;
   - le code doit compiler / tourner avant de demander la review.
5. Avant d'ouvrir la PR, mettre sa branche à jour avec `main` :
   ```bash
   git checkout main && git pull
   git checkout ma-branche && git merge main
   ```
6. Supprimer la branche une fois la PR mergée.

## Formats et conventions d'API

> Section à compléter au fur et à mesure que l'API évolue. Toute modification d'un endpoint ou d'un format doit être mise à jour ici **dans la même PR**.

### Généralités

- Base URL (dev) : `http://localhost:8080/api`
- Format d'échange : **JSON** (`Content-Type: application/json`)
- Noms des champs JSON en `camelCase`
- Dates au format **ISO 8601** (`2026-11-17T14:30:00`)
- Les URL sont en minuscules, au pluriel, séparées par des `-`

### Méthodes HTTP

| Méthode  | Usage                    |
|----------|--------------------------|
| `GET`    | Lire une ressource       |
| `POST`   | Créer une ressource      |
| `PUT`    | Modifier une ressource   |
| `DELETE` | Supprimer une ressource  |

### Endpoints

| Méthode | URL                          | Description                                                                 | Corps de requête | Réponse                                   |
|---------|------------------------------|-----------------------------------------------------------------------------|------------------|-------------------------------------------|
| `POST`  | `/api/upload-carte`          | Charge une carte (remplace la précédente, oublie les livraisons)            | `file` (XML plan)       | `200` + `{"intersections": n, "troncons": m}`, `400` si fichier invalide (l'ancienne carte est gardée) |
| `POST`  | `/api/upload-livraisons`     | Charge une demande de livraisons sur la carte chargée                       | `file` (XML demande)    | `200` + `DemandeLivraisons`, `409` si pas de carte, `400` si fichier invalide ou adresse absente de la carte |
| `GET`   | `/api/route-graph`           | Graphe de la carte chargée (intersections + tronçons)                       | -                | `200` + `RouteGraph`, `409` si pas de carte |
| `GET`   | `/api/tournee`               | Tous les coursiers avec leur tournée (calculée à l'assignation, `null` si aucune livraison) | -  | `200` + `Coursier[]`, `409` si pas de carte / livraisons |
| `POST`  | `/api/add-coursiers`         | Ajoute des coursiers (le backend attribue les ids)                          | JSON `[{prenom, nom}]` | `200` + `Coursier[]`, `409` si pas de carte |
| `GET`   | `/api/coursiers`             | Liste des coursiers                                                         | -                | `200` + `Coursier[]`, `409` si pas de carte |
| `GET`   | `/api/coursiers/{id}`        | Un coursier                                                                 | -                | `200` + `Coursier`, `404` si id inconnu |
| `POST`  | `/api/coursiers/{id}/assignLivraisons` | Assigne des livraisons au coursier et calcule sa tournée          | JSON `[id, ...]` | `200` + `Coursier`, `404` coursier/livraison inconnu, `409` pas de livraisons, `422` tournée impossible |
| `DELETE`| `/api/deleteAllLivraisonsForCoursiers` | Retire les livraisons de tous les coursiers                       | -                | `200`, `409` si pas de carte |

Les deux `upload-*` reçoivent le fichier en `multipart/form-data` (champ `file`), pas en JSON. Les fichiers uploadés ne sont pas enregistrés sur le disque.


### Exemple de réponse

`POST /api/upload-livraisons`

```json
{
  "adresse_entrepot": 25327124,
  "heure_depart": 28800,
  "livraisons": [
    {
      "id": 1,
      "adresse_enlevement": 26464256,
      "adresse_livraison": 239603465,
      "duree_enlevement": 0,
      "duree_livraison": 600
    }
  ]
}
```

`heure_depart` est en secondes après minuit (08:00 → 28800), les durées en secondes.

### Format des erreurs

Toutes les erreurs de l'API ont le même format :

```json
{
  "erreur": {
    "code": "ADRESSES_INCONNUES",
    "message": "Adresses absentes de la carte : [123] (mauvaise carte ?)",
    "details": { "adresses": [123] }
  }
}
```

- `code` : identifiant **stable**, à tester côté frontend pour réagir à un cas précis ;
- `message` : texte lisible, à afficher tel quel à l'utilisateur (il peut changer) ;
- `details` : données complémentaires, souvent vide (`{}`).

| HTTP  | `code`                    | Quand                                                     |
|-------|---------------------------|-----------------------------------------------------------|
| `400` | `CARTE_INVALIDE`          | Fichier de carte illisible ou mal formé                   |
| `400` | `LIVRAISONS_INVALIDES`    | Fichier de livraisons illisible ou mal formé              |
| `400` | `ADRESSES_INCONNUES`      | Adresse de la demande absente de la carte (`details.adresses`) |
| `409` | `CARTE_NON_CHARGEE`       | Action qui demande une carte, avant tout upload de carte  |
| `409` | `LIVRAISONS_NON_CHARGEES` | Calcul de tournée sans livraisons chargées                |
| `409` | `AUCUNE_LIVRAISON_ASSIGNEE` | Calcul de tournée d'un coursier sans livraison (`details.coursier`) |
| `404` | `COURSIER_INCONNU`        | Id de coursier inexistant (`details.coursier`)            |
| `404` | `LIVRAISONS_INCONNUES`    | Id(s) de livraison inexistant(s) (`details.livraisons`)   |
| `422` | `TOURNEE_IMPOSSIBLE`      | Arrêts inaccessibles depuis l'entrepôt                    |
| `422` | `REQUETE_INVALIDE`        | Requête mal construite (ex : champ `file` absent ; `details.erreurs`) |
| `404`… | `HTTP_404`…              | Route inconnue, méthode non autorisée...                  |
| `500` | `ERREUR_INTERNE`          | Bug côté serveur (la trace est dans les logs du backend)  |

Côté backend, les erreurs prévues sont des sous-classes de `ErreurMetier`
(voir `backend/erreurs.py`). Le code métier les lève sans connaître HTTP ;
`api.py` les convertit en réponse JSON. Pour un nouveau cas d'erreur, créer
une sous-classe seulement si le frontend doit y réagir différemment ; sinon,
réutiliser une classe existante avec un autre message.

## Formats des fichiers d'entree

### Fichier des livraisons a faire (XML)

Charge par le backend via `livraisons.charger_livraisons(chemin)`.

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<demandeDeLivraisons>
    <entrepot adresse="25327124" heureDepart="08:00"/>
    <livraison adresseEnlevement="26464256" adresseLivraison="239603465"
               dureeEnlevement="0" dureeLivraison="600"/>
</demandeDeLivraisons>
```

| Element / attribut    | Type      | Obligatoire | Remarques                                  |
|-----------------------|-----------|-------------|--------------------------------------------|
| `entrepot/adresse`    | entier    | oui         | Identifiant d'intersection de la carte     |
| `entrepot/heureDepart`| `HH:MM` ou `HH:MM:SS` | oui | Heure de depart des coursiers (ex. `08:00` ou `8:0:0`) |
| `livraison/adresseEnlevement` | entier | oui  | Adresse d'enlevement                      |
| `livraison/adresseLivraison`  | entier | oui  | Adresse de livraison                      |
| `livraison/dureeEnlevement`  | entier (secondes) | oui | Doit etre >= 0                |
| `livraison/dureeLivraison`   | entier (secondes) | oui | Doit etre >= 0                |


## Documentation

- **Chaque nouvelle feature (frontend ou backend) doit documenter les formats d'échange** pour que les deux côtés communiquent correctement :
  - côté backend : l'URL, la méthode, le format **attendu** en entrée (corps, paramètres) et le format **renvoyé** (réponse + codes d'erreur) ;
  - côté frontend : ce que le front **envoie** et ce qu'il **attend** en retour.
  - Cette documentation est ajoutée (ou mise à jour) dans la section « Formats et conventions d'API » ci-dessus ou dans `docs/`, **dans la même PR que la feature**. Une PR qui touche à la communication front/back sans documentation des formats n'est pas mergée.
- Les diagrammes (classes, séquence, cas d'utilisation...) vont dans `docs/`, avec leur **source éditable** (ex. `.puml`, `.drawio`) en plus de l'export image.
- Toute évolution du code qui change le modèle doit mettre à jour les diagrammes concernés dans la même PR.
