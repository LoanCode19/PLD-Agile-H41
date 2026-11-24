from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from backend.livraisons.parseur_livraisons import DemandeLivraisons, charger_livraisons
from backend.routeGraph.routeGraph import RouteGraph
from backend.shortestPath.shortestPathFinder import ShortestPathFinder

RESSOURCES = Path(__file__).resolve().parent.parent / "ressources"

app = FastAPI()


class ListeLivreurs(BaseModel):
    livreurs: list[str] = Field(min_length=1)

    @field_validator("livreurs")
    @classmethod
    def valider_livreurs(cls, livreurs: list[str]) -> list[str]:
        noms = [nom.strip() for nom in livreurs]

        if any(not nom for nom in noms):
            raise ValueError("Chaque livreur doit avoir un nom")

        noms_normalises = [nom.lower() for nom in noms]
        if len(noms_normalises) != len(set(noms_normalises)):
            raise ValueError("Les noms des livreurs doivent être uniques")

        return noms


# Autorise le frontend Vite (dev) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/route-graph", response_model=RouteGraph)
async def get_route_graph():
    graph = RouteGraph()
    graph.construct_from_xml(RESSOURCES / "grandPlan.xml")
    return {graph}


@app.get("/api/getTestListLivraison", response_model=DemandeLivraisons)
async def get_list_livraison():
    return {"deliveries": charger_livraisons(RESSOURCES / "demandeGrand9.xml")}


@app.get("/api/getTestShortestPath")
async def get_shortest_path():
    livraisons = charger_livraisons(RESSOURCES / "demandeGrand9.xml")
    graph = RouteGraph()
    graph.construct_from_xml(RESSOURCES / "grandPlan.xml")
    shortest_path = ShortestPathFinder(graph, livraisons)
    return {"shortest_path": shortest_path.getBestRoute()}


@app.post("/api/livreurs", response_model=ListeLivreurs, status_code=201)
async def create_livreurs(liste: ListeLivreurs):
    return liste
