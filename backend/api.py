from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from livraisons.parseur_livraisons import DemandeLivraisons
from planification.planification import Planification
from routeGraph.routeGraph import RouteGraph
from tournee.tournee import Tournee

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
        planification.calculer_tournee()
        return planification.coursier
    except ValueError as e:  # aucune demande chargée, adresse inconnue...
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/livreurs", response_model=ListeLivreurs, status_code=201)
async def create_livreurs(liste: ListeLivreurs):
    return liste