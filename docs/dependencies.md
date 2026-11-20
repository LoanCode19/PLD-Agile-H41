# Dépendances

Liste des bibliothèques utilisées dans le projet, qui les utilise et où.
À mettre à jour à chaque ajout ou suppression d'un import.

## Environnement

| Outil  | Version testée |
|--------|----------------|
| Python | 3.14           |

## Bibliothèques externes (à installer)

| Dépendance | Version | Utilisée par         | Où                           | Rôle                  |
|------------|---------|----------------------|------------------------------|-----------------------|
| pytest     | 9.2.0   | Tests du backend     | `backend/routeGraph/test_routeGraph.py` | Lancer les tests unitaires |

Installation :

```bash
pip install pytest
```

## Bibliothèque standard Python (rien à installer)

| Module                  | Utilisé par          | Où                           | Rôle                                   |
|-------------------------|----------------------|------------------------------|----------------------------------------|
| `xml.etree.ElementTree` | `RouteGraph`         | `backend/routeGraph/routeGraph.py`      | Lire les plans XML (`noeud`, `troncon`) |
| `dataclasses`           | `Node`, `Edge`       | `backend/routeGraph/routeGraph.py`      | Définir les classes de données          |
| `os`                    | Tests du backend     | `backend/routeGraph/test_routeGraph.py` | Construire les chemins vers `ressources/` |

## Frontend

| Dépendance | Version | Utilisée par | Où                     | Rôle                                  |
|------------|---------|--------------|------------------------|---------------------------------------|
| Node.js    | 24      | Front        | -                      | Exécuter npm et Vite                  |
| vite       | ^8.3.6  | Front        | `frontend/package.json`| Serveur de dev et build du front      |
| leaflet    | ^1.9.4  | Front        | `frontend/src/main.js` | Afficher une carte interactive centrée sur Lyon |

Installation :

```bash
cd frontend
npm install
npm run dev
```
