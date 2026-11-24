from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.livraisons.parseur_livraisons import DemandeLivraisons
from backend.planification.planification import Planification
from backend.routeGraph.routeGraph import RouteGraph
from backend.tournee.tournee import Tournee

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


@app.get("/api/route-graph")
async def get_route_graph():
    return planification.carte


@app.get("/api/getTestListLivraison", response_model=DemandeLivraisons)
async def get_list_livraison():
    return planification.charger_demandes(RESSOURCES / "demandeGrand9.xml")


@app.get("/api/getTestShortestPath", response_model=Tournee)
async def get_shortest_path():
    try:
        return planification.calculer_tournee()
    except ValueError as e:  # aucune demande chargée, adresse inconnue...
        raise HTTPException(status_code=400, detail=str(e)) from e
