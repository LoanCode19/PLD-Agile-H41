import logging
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from coursier.coursier import Coursier
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from erreurs import CarteNonChargee, ErreurMetier
from livraisons.parseur_livraisons import DemandeLivraisons
from planification.planification import Planification
from routeGraph.routeGraph import RouteGraph

logger = logging.getLogger(__name__)

app = FastAPI()


# --- Gestion des erreurs -----------------------------------------------------
# Toutes les erreurs sont renvoyées au même format JSON :
#     {"erreur": {"code": "...", "message": "...", "details": {...}}}
# (voir erreurs.py et le README).

def reponse_erreur(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    """Construit une réponse d'erreur au format commun."""
    return JSONResponse(
        status_code=status,
        content={"erreur": {"code": code, "message": message, "details": details or {}}},
    )


@app.exception_handler(ErreurMetier)
async def gerer_erreur_metier(request: Request, e: ErreurMetier):
    """Erreur prévue (fichier invalide, données manquantes...)."""
    return reponse_erreur(e.status, e.code, e.message, e.details)


@app.exception_handler(RequestValidationError)
async def gerer_requete_invalide(request: Request, e: RequestValidationError):
    """Requête mal construite par le client (ex : champ `file` absent)."""
    return reponse_erreur(422, "REQUETE_INVALIDE", "Requête invalide", {"erreurs": e.errors()})


@app.exception_handler(StarletteHTTPException)
async def gerer_http(request: Request, e: StarletteHTTPException):
    """Erreurs HTTP de FastAPI lui-même (404 route inconnue, 405...)."""
    return reponse_erreur(e.status_code, f"HTTP_{e.status_code}", str(e.detail))


# Erreur NON prévue = bug. On la rattrape dans un middleware (et non avec
# un exception_handler(Exception)) pour que la réponse 500 passe encore par
# le middleware CORS : sinon le navigateur la bloque et le frontend ne peut
# pas lire le message. Ce middleware doit donc être déclaré AVANT le CORS.
@app.middleware("http")
async def intercepter_bugs(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Erreur inattendue sur %s %s", request.method, request.url.path)
        return reponse_erreur(500, "ERREUR_INTERNE", "Erreur interne du serveur")


# Autorise le frontend Vite (dev) à appeler l'API.
# Déclaré APRÈS intercepter_bugs : le dernier middleware déclaré est le plus
# externe, donc le CORS ajoute bien ses en-têtes aux réponses 500.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- État ----------------------------------------------------------------------

# Une seule planification, gardée en mémoire entre les appels.
# None tant qu'aucune carte n'a été uploadée.
planification: Planification | None = None
current_coursier_id = 1  # l'id du coursier pour être sûr d'éviter les conflits


def lire_upload(file: UploadFile, charger):
    """Copie le fichier uploadé dans un fichier temporaire, le passe à
    `charger(chemin)` puis supprime le fichier temporaire.
    Les erreurs de `charger` remontent telles quelles (voir gestionnaires)."""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
    try:
        return charger(Path(tmp.name))
    finally:
        os.remove(tmp.name)


def charger_carte(chemin: Path) -> RouteGraph:
    carte = RouteGraph()
    carte.construct_from_xml(chemin)
    if carte.node_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Fichier invalide : ce n'est pas une carte (aucune intersection)",
        )
    return carte


def planification_avec_carte() -> Planification:
    if planification is None:
        raise HTTPException(
            status_code=400, detail="Aucune carte chargée : uploadez d'abord une carte"
        )
    return planification


# --- Routes ----------------------------------------------------------------------

@app.post("/api/upload-carte")
async def upload_carte(file: UploadFile = File(...)):
    """Charge une nouvelle carte. Les livraisons déjà chargées sont oubliées.
    Si la carte est invalide, l'ancienne est conservée."""
    global planification
    carte = lire_upload(file, charger_carte)
    planification = Planification(carte)
    return {"intersections": carte.node_count, "troncons": carte.edge_count}


@app.post("/api/upload-livraisons", response_model=DemandeLivraisons)
async def upload_livraisons(file: UploadFile = File(...)):
    """Charge une demande de livraisons sur la carte déjà chargée.
    Si le fichier est invalide, plus aucune livraison n'est chargée."""
    p = planification_avec_carte()

    def charger(chemin: Path) -> DemandeLivraisons:
        p.demande = (
            None  # si le nouveau fichier est invalide, plus aucune livraison chargée
        )
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


@app.get("/api/tournee", response_model=list[Coursier])
async def get_tournee():
    """Calcule la tournée pour la carte et les livraisons uploadées."""
    p = planification_avec_carte()
    if p.demande is None:
        raise HTTPException(
            status_code=400,
            detail="Aucune livraison chargée : uploadez d'abord les livraisons",
        )
    try:
        return [coursier for coursier in p.coursiers.values()]
    except ValueError as e:  # arrêt inaccessible...
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/add-coursiers", response_model=list[Coursier])
async def add_coursier(coursiers: list[Coursier]):
    """Ajoute les coursiers à ceux qui existent déjà. Les ids continuent
    depuis le dernier attribué (le compteur n'est jamais remis à 1)."""
    global current_coursier_id
    p = planification_avec_carte()
    for coursier in coursiers:
        coursier.id = current_coursier_id
        current_coursier_id += 1
        p.coursiers[coursier.id] = coursier
    return coursiers


@app.get("/api/coursiers", response_model=list[Coursier])
async def get_coursiers():
    """Retourne la liste des coursiers de la planification."""
    global planification
    if planification is None:
        raise HTTPException(
            status_code=400, detail="Aucune carte chargée : uploadez d'abord une carte"
        )
    return list(planification.coursiers.values())


@app.get("/api/coursiers/{id}", response_model=Coursier)
def getCoursierById(id: int):
    """Retourne le coursier correspondant à l'id donné."""
    p = planification_avec_carte()
    if id not in p.coursiers:
        raise HTTPException(status_code=404, detail=f"Aucun coursier avec l'id {id}")
    return p.coursiers[id]


@app.post("/api/coursiers/{id}/assignLivraisons", response_model=Coursier)
def assignLivraisonsToCoursier(id: int, livraisons: list[int]):
    """Assigne les livraisons (par leurs ids, ex. [1, 3]) au coursier et
    calcule sa tournée.

    La liste remplace les livraisons qu'il avait avant ; une liste vide le
    laisse sans livraison ni tournée. En cas d'erreur, le coursier n'est pas
    modifié.
    """
    p = planification_avec_carte()
    if id not in p.coursiers:
        raise HTTPException(status_code=404, detail=f"Aucun coursier avec l'id {id}")
    if p.demande is None:
        raise HTTPException(
            status_code=400,
            detail="Aucune livraison chargée : uploadez d'abord les livraisons",
        )

    # On vérifie tous les ids avant de toucher au coursier.
    par_id = {l.id: l for l in p.demande.livraisons}
    inconnues = [i for i in livraisons if i not in par_id]
    if inconnues:
        raise HTTPException(
            status_code=404, detail=f"Aucune livraison avec l'id {inconnues}"
        )

    coursier = p.coursiers[id]
    anciennes, ancienne_tournee = coursier.livraisons, coursier.tournee
    # dict.fromkeys : retire les doublons en gardant l'ordre.
    coursier.livraisons = [par_id[i] for i in dict.fromkeys(livraisons)]

    if not coursier.livraisons:
        coursier.tournee = None
        return coursier
    try:
        p.calculer_tournee(id)
    except ValueError as e:  # arrêt inaccessible... : on remet l'état d'avant
        coursier.livraisons, coursier.tournee = anciennes, ancienne_tournee
        raise HTTPException(status_code=400, detail=str(e)) from e
    return coursier


@app.delete("/api/deleteAllLivraisonsForCoursiers")
def deleteAllLivraisons():
    """Supprime toutes les livraisons de la planification."""
    p = planification_avec_carte()
    for coursier in p.coursiers.values():
        coursier.livraisons = []
        coursier.tournee = None
