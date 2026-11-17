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

Aucune dépendance pour l'instant.
