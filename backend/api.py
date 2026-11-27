import logging
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from coursier.coursier import Coursier
from erreurs import CarteNonChargee, ErreurMetier, LivraisonsInconnues, LivraisonsNonChargees
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
    """FichierCarteInvalide si le fichier n'est pas une carte valide."""
    carte = RouteGraph()
    carte.construct_from_xml(chemin)
    return carte


def planification_avec_carte() -> Planification:
    if planification is None:
        raise CarteNonChargee()
    return planification


def demande_chargee(p: Planification):
    if p.demande is None:
        raise LivraisonsNonChargees()
    return p.demande


# --- Routes ----------------------------------------------------------------------

@app.post("/api/upload-carte")
async def upload_carte(file: UploadFile = File(...)):
    """Charge une nouvelle carte. Les livraisons et les coursiers déjà
    chargés sont oubliés. Si la carte est invalide, l'ancienne est conservée."""
    global planification
    carte = lire_upload(file, charger_carte)
    planification = Planification(carte)
    return {"intersections": carte.node_count, "troncons": carte.edge_count}


@app.post("/api/upload-livraisons", response_model=DemandeLivraisons)
async def upload_livraisons(file: UploadFile = File(...)):
    """Charge une demande de livraisons sur la carte déjà chargée.
    Si le fichier est invalide, plus aucune livraison n'est chargée."""
    p = planification_avec_carte()
    # charger_demandes vérifie le format ET que les adresses sont sur la carte
    return lire_upload(file, p.charger_demandes)


@app.get("/api/route-graph")
async def get_route_graph():
    return planification_avec_carte().carte


@app.get("/api/tournee", response_model=list[Coursier])
async def get_tournee():
    """Renvoie tous les coursiers avec leur tournée. La tournée est calculée
    lors de l'assignation (assignLivraisons) ; elle vaut null pour un coursier
    sans livraison."""
    p = planification_avec_carte()
    demande_chargee(p)
    return list(p.coursiers.values())


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
    return list(planification_avec_carte().coursiers.values())


@app.get("/api/coursiers/{id}", response_model=Coursier)
def getCoursierById(id: int):
    """Retourne le coursier correspondant à l'id donné."""
    return planification_avec_carte().coursier(id)  # CoursierInconnu -> 404


@app.post("/api/coursiers/{id}/assignLivraisons", response_model=Coursier)
def assignLivraisonsToCoursier(id: int, livraisons: list[int]):
    """Assigne les livraisons (par leurs ids, ex. [1, 3]) au coursier et
    calcule sa tournée.

    La liste remplace les livraisons qu'il avait avant ; une liste vide le
    laisse sans livraison ni tournée. En cas d'erreur, le coursier n'est pas
    modifié.
    """
    p = planification_avec_carte()
    coursier = p.coursier(id)
    demande = demande_chargee(p)

    # On vérifie tous les ids avant de toucher au coursier.
    par_id = {l.id: l for l in demande.livraisons}
    inconnues = [i for i in livraisons if i not in par_id]
    if inconnues:
        raise LivraisonsInconnues(inconnues)

    anciennes, ancienne_tournee = coursier.livraisons, coursier.tournee
    # dict.fromkeys : retire les doublons en gardant l'ordre.
    coursier.livraisons = [par_id[i] for i in dict.fromkeys(livraisons)]

    if not coursier.livraisons:
        coursier.tournee = None
        return coursier
    try:
        p.calculer_tournee(id)
    except Exception:
        # Quelle que soit l'erreur (tournée impossible, bug...), on remet le
        # coursier dans son état d'avant, puis on laisse l'erreur remonter
        # jusqu'aux gestionnaires d'erreurs.
        coursier.livraisons, coursier.tournee = anciennes, ancienne_tournee
        raise
    return coursier


@app.delete("/api/deleteAllLivraisonsForCoursiers")
def deleteAllLivraisons():
    """Retire les livraisons (et donc la tournée) de tous les coursiers."""
    p = planification_avec_carte()
    for coursier in p.coursiers.values():
        coursier.livraisons = []
        coursier.tournee = None
