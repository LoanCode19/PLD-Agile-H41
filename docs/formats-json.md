# Formats JSON attendus par le front

Le front reçoit uniquement les **intersections**.
Pour l'instant les données sont en dur dans `frontend/src/sampleData.json` ; le backend devra renvoyer exactement ce format.

## Intersections

Affichées brutes, ligne par ligne, par `displayJson(json, zone)` dans `frontend/src/display.js`.

```json
{
  "intersections": [
    { "id": "25175791", "latitude": 45.75406, "longitude": 4.857418 },
    { "id": "2129259178", "latitude": 45.750404, "longitude": 4.8744674 }
  ]
}
```

Un objet contenant la clé `intersections`, qui est une liste. Chaque intersection contient :

| Champ       | Type   | Description                   |
|-------------|--------|-------------------------------|
| `id`        | string | Identifiant de l'intersection |
| `latitude`  | number | Latitude                      |
| `longitude` | number | Longitude                     |
