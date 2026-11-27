"""Point d'entrée de l'API vers le modèle : une carte, des coursiers.

Chaque coursier a les livraisons qu'on lui assigne et sa propre tournée.
"""

from pathlib import Path

from coursier.coursier import Coursier
from livraisons.parseur_livraisons import DemandeLivraisons, charger_livraisons
from routeGraph.routeGraph import RouteGraph
from shortestPath.shortestPathFinder import ShortestPathFinder
from tournee.tournee import Tournee


class Planification:
    """La carte, les coursiers et la demande de livraisons chargée.

    Attributes:
        carte: le plan de la ville.
        coursiers: les coursiers par id ; vide tant qu'on n'en a pas créé
            (sans coursier, aucune tournée ne peut être calculée).
        demande: la demande chargée ; None tant qu'aucun fichier ne l'a été.
    """

    def __init__(self, carte: RouteGraph):
        self.carte = carte
        self.coursiers: dict[int, Coursier] = {}
        self.demande: DemandeLivraisons | None = None

    def charger_demandes(self, fichier: str | Path) -> DemandeLivraisons:
        """Charge un fichier XML de demandes. Les livraisons et la tournée de
        chaque coursier sont effacées, même si le fichier est invalide : elles
        portaient sur l'ancienne demande.

        Raises:
            FichierLivraisonsInvalide: fichier illisible ou mal formé.
        """
        for coursier in self.coursiers.values():
            coursier.livraisons = []
            coursier.tournee = None
        self.demande = charger_livraisons(fichier)
        return self.demande

    def calculer_tournee(self, id: int) -> Tournee:
        """Calcule la tournée du coursier pour les livraisons qui lui sont
        assignées (la demande chargée donne l'entrepôt et l'heure de départ).

        Raises:
            ValueError: aucune demande chargée, adresse absente de la carte
                ou arrêt inaccessible.
        """
        if self.demande is None:
            raise ValueError("Aucune demande chargée")
        if not self.coursiers[id].livraisons:
            raise ValueError(f"Aucune livraison assignée au coursier {id}")
        self.coursiers[id].tournee = ShortestPathFinder(
            self.carte, self.demande, self.coursiers[id].livraisons
        ).calculer_tournee()
        return self.coursiers[id].tournee
