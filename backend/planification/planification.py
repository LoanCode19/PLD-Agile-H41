"""Point d'entrée de l'API vers le modèle : une carte, un coursier.

Pour l'instant il n'y a qu'un seul coursier : toutes les livraisons de la
demande chargée lui reviennent.
"""

from pathlib import Path

from coursier.coursier import Coursier
from erreurs import AdressesInconnues, LivraisonsNonChargees
from livraisons.parseur_livraisons import DemandeLivraisons, charger_livraisons
from routeGraph.routeGraph import RouteGraph
from shortestPath.shortestPathFinder import ShortestPathFinder
from tournee.tournee import Tournee


class Planification:
    """La carte, l'unique coursier et la demande de livraisons chargée.

    Attributes:
        carte: le plan de la ville.
        coursier: l'unique coursier, à qui reviennent toutes les livraisons.
        demande: la demande chargée ; None tant qu'aucun fichier ne l'a été.
    """

    def __init__(self, carte: RouteGraph):
        self.carte = carte
        self.coursiers = {1: Coursier(1)}
        self.demande: DemandeLivraisons | None = None

    def charger_demandes(self, fichier: str | Path) -> DemandeLivraisons:
        """Charge un fichier XML de demandes. Les livraisons et la tournée de
        chaque coursier sont effacées, même si le fichier est invalide : elles
        portaient sur l'ancienne demande.

        Si le fichier est refusé, l'ancienne demande est oubliée aussi :
        aucune demande n'est alors chargée.

        Raises:
            FichierLivraisonsInvalide: fichier illisible ou mal formé.
            AdressesInconnues: une adresse n'existe pas sur la carte.
        """
        # On oublie d'abord l'ancienne demande : si le nouveau fichier est
        # refusé (exception plus bas), aucune demande ne reste chargée.
        self.demande = None
        self.coursier.livraisons = []
        self.coursier.tournee = None

        demande = charger_livraisons(fichier)

        # Le parseur ne vérifie que le format du fichier. On contrôle ici que
        # chaque adresse (entrepôt, enlèvements, livraisons) existe sur la
        # carte chargée avant d'accepter la demande : un fichier prévu pour
        # une autre carte est ainsi refusé dès l'upload.
        adresses = [demande.adresse_entrepot]
        for livraison in demande.livraisons:
            adresses += [livraison.adresse_enlevement, livraison.adresse_livraison]
        inconnues = [a for a in adresses if a not in self.carte]
        if inconnues:
            raise AdressesInconnues(inconnues)

        for coursier in self.coursiers.values():
            coursier.livraisons = []
            coursier.tournee = None
    
        self.demande = demande
        self.coursier.livraisons = list(demande.livraisons)
        return demande

    def calculer_tournee(self, id: int) -> Tournee:
        """Calcule la tournée du coursier pour les livraisons qui lui sont
        assignées (la demande chargée donne l'entrepôt et l'heure de départ).

        Raises:
            LivraisonsNonChargees: aucune demande chargée.
            TourneeImpossible: un arrêt est inaccessible.
        """
        if self.demande is None:
<<<<<<< HEAD
            raise LivraisonsNonChargees()
        self.coursier.tournee = ShortestPathFinder(
            self.carte, self.demande
=======
            raise ValueError("Aucune demande chargée")
        if not self.coursiers[id].livraisons:
            raise ValueError(f"Aucune livraison assignée au coursier {id}")
        self.coursiers[id].tournee = ShortestPathFinder(
            self.carte, self.demande, self.coursiers[id].livraisons
>>>>>>> 5cd0ed38cde6a615430f739c7cfe6b84364501d3
        ).calculer_tournee()
        return self.coursiers[id].tournee
