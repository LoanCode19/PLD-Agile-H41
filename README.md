# PLD Agile - H41

Guide des bonnes pratiques à respecter sur ce dépôt.

## Structure du dépôt

| Dossier     | Contenu                                                                 |
|-------------|-------------------------------------------------------------------------|
| `frontend/` | Tout le code du front (interface, composants, appels à l'API...)        |
| `backend/`  | Tout le code du back (API, logique métier, accès aux données...)        |
| `docs/`     | Toute la documentation : diagrammes de classes, de séquence, maquettes, comptes rendus, etc. |

Ne pas mélanger : pas de code front dans `backend/`, pas de doc dans `frontend/`, etc.

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

- Base URL (dev) : `http://localhost:8080/api`  *(à adapter)*
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

| Méthode | URL                | Description                | Corps de requête | Réponse        |
|---------|--------------------|----------------------------|------------------|----------------|
| `GET`   | `/api/exemples`    | Liste des exemples         | -                | `200` + liste  |
| `GET`   | `/api/exemples/{id}` | Détail d'un exemple      | -                | `200` + objet  |
| `POST`  | `/api/exemples`    | Crée un exemple            | voir ci-dessous  | `201` + objet  |

*(Remplacer les lignes d'exemple par les vrais endpoints.)*

### Exemple de requête / réponse

`POST /api/exemples`

```json
{
  "nom": "Exemple",
  "dateCreation": "2026-11-17T14:30:00"
}
```

Réponse `201 Created` :

```json
{
  "id": 1,
  "nom": "Exemple",
  "dateCreation": "2026-11-17T14:30:00"
}
```

### Format des erreurs

```json
{
  "status": 400,
  "message": "Description lisible de l'erreur"
}
```

| Code  | Signification                      |
|-------|------------------------------------|
| `200` | OK                                 |
| `201` | Ressource créée                    |
| `400` | Requête invalide                   |
| `404` | Ressource introuvable              |
| `500` | Erreur serveur                     |

## Documentation

- Les diagrammes (classes, séquence, cas d'utilisation...) vont dans `docs/`, avec leur **source éditable** (ex. `.puml`, `.drawio`) en plus de l'export image.
- Toute évolution du code qui change le modèle doit mettre à jour les diagrammes concernés dans la même PR.
