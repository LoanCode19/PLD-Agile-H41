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
        self.coursier = Coursier(1)
        self.demande: DemandeLivraisons | None = None

    def charger_demandes(self, fichier: str | Path) -> DemandeLivraisons:
        """Charge un fichier XML de demandes ; ses livraisons reviennent au
        coursier. L'ancienne tournée est effacée.

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

        self.demande = demande
        self.coursier.livraisons = list(demande.livraisons)
        return demande

    def calculer_tournee(self) -> Tournee:
        """Calcule la tournée du coursier pour la demande chargée.

        Raises:
            LivraisonsNonChargees: aucune demande chargée.
            TourneeImpossible: un arrêt est inaccessible.
        """
        if self.demande is None:
            raise LivraisonsNonChargees()
        self.coursier.tournee = ShortestPathFinder(
            self.carte, self.demande
        ).calculer_tournee()
        return self.coursier.tournee
