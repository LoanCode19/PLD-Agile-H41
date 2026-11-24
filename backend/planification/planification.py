"""Point d'entrée de l'API vers le modèle : une carte, un coursier.

Pour l'instant il n'y a qu'un seul coursier : toutes les livraisons de la
demande chargée lui reviennent.
"""

from pathlib import Path

from backend.coursier.coursier import Coursier
from backend.livraisons.parseur_livraisons import DemandeLivraisons, charger_livraisons
from backend.routeGraph.routeGraph import RouteGraph
from backend.shortestPath.shortestPathFinder import ShortestPathFinder
from backend.tournee.tournee import Tournee


class Planification:
    """La carte, l'unique coursier et la demande de livraisons chargée.

    Attributes:
        carte: le plan de la ville.
        coursier: l'unique coursier, à qui reviennent toutes les livraisons.
        demande: la demande chargée ; None tant qu'aucun fichier ne l'a été.
    """

    def __init__(self, carte: RouteGraph):
        self.carte = carte
        self.coursier = Coursier(1)
        self.demande: DemandeLivraisons | None = None

    def charger_demandes(self, fichier: str | Path) -> DemandeLivraisons:
        """Charge un fichier XML de demandes ; ses livraisons reviennent au
        coursier. L'ancienne tournée est effacée.

        Raises:
            FichierLivraisonsInvalide: fichier illisible ou mal formé.
        """
        self.demande = charger_livraisons(fichier)
        self.coursier.livraisons = list(self.demande.livraisons)
        self.coursier.tournee = None
        return self.demande

    def calculer_tournee(self) -> Tournee:
        """Calcule la tournée du coursier pour la demande chargée.

        Raises:
            ValueError: aucune demande chargée, adresse absente de la carte
                ou arrêt inaccessible.
        """
        if self.demande is None:
            raise ValueError("Aucune demande chargée")
        self.coursier.tournee = ShortestPathFinder(
            self.carte, self.demande
        ).calculer_tournee()
        return self.coursier.tournee
