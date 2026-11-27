"""Point d'entrée de l'API vers le modèle : une carte, des coursiers et la
demande de livraisons chargée.

Les livraisons de la demande ne sont assignées à aucun coursier au
chargement : c'est l'API (route assignLivraisons) qui les répartit.
"""

from pathlib import Path

from coursier.coursier import Coursier
from erreurs import (
    AdressesInconnues,
    AucuneLivraisonAssignee,
    CoursierInconnu,
    LivraisonsNonChargees,
)
from livraisons.parseur_livraisons import DemandeLivraisons, charger_livraisons
from routeGraph.routeGraph import RouteGraph
from shortestPath.shortestPathFinder import ShortestPathFinder
from tournee.tournee import Tournee


class Planification:
    """La carte, les coursiers et la demande de livraisons chargée.

    Attributes:
        carte: le plan de la ville.
        coursiers: les coursiers par id (le coursier 1 existe par défaut).
        demande: la demande chargée ; None tant qu'aucun fichier ne l'a été.
    """

    def __init__(self, carte: RouteGraph):
        self.carte = carte
        self.coursiers = {1: Coursier(1)}
        self.demande: DemandeLivraisons | None = None

    def coursier(self, id: int) -> Coursier:
        """Le coursier d'id donné.

        Raises:
            CoursierInconnu: aucun coursier avec cet id.
        """
        if id not in self.coursiers:
            raise CoursierInconnu(id)
        return self.coursiers[id]

    def charger_demandes(self, fichier: str | Path) -> DemandeLivraisons:
        """Charge un fichier XML de demandes. Les livraisons et la tournée de
        chaque coursier sont effacées, même si le fichier est refusé : elles
        portaient sur l'ancienne demande. Si le fichier est refusé, aucune
        demande ne reste chargée.

        Raises:
            FichierLivraisonsInvalide: fichier illisible ou mal formé.
            AdressesInconnues: une adresse n'existe pas sur la carte.
        """
        # On oublie d'abord l'ancienne demande et ce qui en dépendait : si le
        # nouveau fichier est refusé (exception plus bas), il ne reste rien.
        self.demande = None
        for coursier in self.coursiers.values():
            coursier.livraisons = []
            coursier.tournee = None

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
        return demande

    def calculer_tournee(self, id: int) -> Tournee:
        """Calcule la tournée du coursier pour les livraisons qui lui sont
        assignées (la demande chargée donne l'entrepôt et l'heure de départ).

        Raises:
            CoursierInconnu: aucun coursier avec cet id.
            LivraisonsNonChargees: aucune demande chargée.
            AucuneLivraisonAssignee: le coursier n'a aucune livraison.
            TourneeImpossible: un arrêt est inaccessible.
        """
        coursier = self.coursier(id)
        if self.demande is None:
            raise LivraisonsNonChargees()
        if not coursier.livraisons:
            raise AucuneLivraisonAssignee(id)
        coursier.tournee = ShortestPathFinder(
            self.carte, self.demande, coursier.livraisons
        ).calculer_tournee()
        return coursier.tournee
