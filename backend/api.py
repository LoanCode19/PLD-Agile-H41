from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.livraisons.parseur_livraisons import charger_livraisons
from backend.routeGraph.routeGraph import RouteGraph
from backend.shortestPath.shortestPathFinder import ShortestPathFinder

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


@app.get("/api/route-graph")
async def get_route_graph():
    graph = RouteGraph()
    graph.construct_from_xml(RESSOURCES / "grandPlan.xml")
    return {graph}


@app.get("/api/getTestListLivraison")
async def get_list_livraison():
    return {"deliveries": charger_livraisons(RESSOURCES / "demandeGrand9.xml")}


@app.get("/api/getTestShortestPath")
async def get_shortest_path():
    livraisons = charger_livraisons(RESSOURCES / "demandeGrand9.xml")
    graph = RouteGraph()
    graph.construct_from_xml(RESSOURCES / "grandPlan.xml")
    shortest_path = ShortestPathFinder(graph, livraisons)
    return {"shortest_path": shortest_path.getBestRoute()}
