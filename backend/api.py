import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from coursier.coursier import Coursier
from livraisons.parseur_livraisons import DemandeLivraisons
from planification.planification import Planification
from routeGraph.routeGraph import RouteGraph

app = FastAPI()

# Autorise le frontend Vite (dev) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Une seule planification, gardée en mémoire entre les appels.
# None tant qu'aucune carte n'a été uploadée.
planification: Planification | None = None


def lire_upload(file: UploadFile, charger):
    """Copie le fichier uploadé dans un fichier temporaire, le passe à
    `charger(chemin)` puis supprime le fichier temporaire.
    Toute erreur de lecture devient une erreur 400."""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
    try:
        return charger(Path(tmp.name))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fichier invalide : {e}") from e
    finally:
        os.remove(tmp.name)


def charger_carte(chemin: Path) -> RouteGraph:
    carte = RouteGraph()
    carte.construct_from_xml(chemin)
    if carte.node_count == 0:
        raise HTTPException(status_code=400, detail="Fichier invalide : ce n'est pas une carte (aucune intersection)")
    return carte


def planification_avec_carte() -> Planification:
    if planification is None:
        raise HTTPException(status_code=400, detail="Aucune carte chargée : uploadez d'abord une carte")
    return planification


@app.post("/api/upload-carte")
async def upload_carte(file: UploadFile = File(...)):
    """Charge une nouvelle carte. Les livraisons déjà chargées sont oubliées."""
    global planification
    carte = lire_upload(file, charger_carte)
    planification = Planification(carte)
    return {"intersections": carte.node_count, "troncons": carte.edge_count}


@app.post("/api/upload-livraisons", response_model=DemandeLivraisons)
async def upload_livraisons(file: UploadFile = File(...)):
    """Charge une demande de livraisons sur la carte déjà chargée."""
    p = planification_avec_carte()

    def charger(chemin: Path) -> DemandeLivraisons:
        p.demande = None  # si le nouveau fichier est invalide, plus aucune livraison chargée
        p.charger_demandes(chemin)
        adresses = [p.demande.adresse_entrepot]
        for l in p.demande.livraisons:
            adresses += [l.adresse_enlevement, l.adresse_livraison]
        inconnues = [a for a in adresses if a not in p.carte]
        if inconnues:
            p.demande = None
            raise HTTPException(
                status_code=400,
                detail=f"Adresses absentes de la carte : {inconnues[:5]} (mauvaise carte ?)",
            )
        return p.demande

    return lire_upload(file, charger)


@app.get("/api/route-graph")
async def get_route_graph():
    return planification_avec_carte().carte


@app.get("/api/tournee", response_model=Coursier)
async def get_tournee():
    """Calcule la tournée pour la carte et les livraisons uploadées."""
    p = planification_avec_carte()
    if p.demande is None:
        raise HTTPException(status_code=400, detail="Aucune livraison chargée : uploadez d'abord les livraisons")
    try:
        p.calculer_tournee()
        return p.coursier
    except ValueError as e:  # arrêt inaccessible...
        raise HTTPException(status_code=400, detail=str(e)) from e
