from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from livraisons.parseur_livraisons import DemandeLivraisons
from planification.planification import Planification
from routeGraph.routeGraph import RouteGraph
from coursier.coursier import Coursier
import shutil

RESSOURCES = Path(__file__).resolve().parent.parent / "ressources"

app = FastAPI()

# Autorise le frontend Vite (dev) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def charger_carte(chemin: Path) -> RouteGraph:
    carte = RouteGraph()
    carte.construct_from_xml(chemin)
    return carte


# Une seule planification, gardée en mémoire entre les appels.
planification = Planification(charger_carte(RESSOURCES / "grandPlan.xml"))
planification.charger_demandes(RESSOURCES / "demandeGrand9Depassement.xml") #a enlever pour le test de l'API


@app.get("/api/route-graph")
async def get_route_graph():
    return planification.carte


@app.get("/api/getTestListLivraison", response_model=DemandeLivraisons)
async def get_list_livraison():
    return planification.charger_demandes(RESSOURCES / "demandeMoyen5.xml")

@app.get("/api/getTestShortestPath", response_model=Coursier)
async def get_shortest_path():
    try:
        planification.calculer_tournee()
        return planification.coursier
    except ValueError as e:  # aucune demande chargée, adresse inconnue...
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/upload-livraisons", response_model=DemandeLivraisons)
async def upload_livraisons(file: UploadFile = File(...)):
    try:
        destination = RESSOURCES / Path(file.filename).name  # .name : empeche "../" dans le nom
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Charge et retourne le modèle DemandeLivraisons parsed par ton parseur
        return planification.charger_demandes(destination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload des livraisons : {str(e)}")


@app.post("/api/upload-carte")
async def upload_carte(file: UploadFile = File(...)):
    try:
        destination = RESSOURCES / Path(file.filename).name  # .name : empeche "../" dans le nom
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        global planification
        nouvelle_carte = charger_carte(destination)
        planification = Planification(nouvelle_carte)
        
        return {"message": "Fichier de carte uploadé avec succès", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload de la carte : {str(e)}")