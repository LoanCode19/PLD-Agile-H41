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
    return carte


def planification_avec_carte() -> Planification:
    if planification is None:
        raise CarteNonChargee()
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
    # charger_demandes vérifie le format ET que les adresses sont sur la carte
    return lire_upload(file, p.charger_demandes)


@app.get("/api/route-graph")
async def get_route_graph():
    return planification_avec_carte().carte


@app.get("/api/tournee", response_model=Coursier)
async def get_tournee():
    """Calcule la tournée pour la carte et les livraisons uploadées."""
    p = planification_avec_carte()
    p.calculer_tournee()  # LivraisonsNonChargees si aucune demande
    return p.coursier
