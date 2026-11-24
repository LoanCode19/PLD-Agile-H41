"""Un coursier et les livraisons qui lui sont assignées."""

from dataclasses import dataclass, field

from backend.livraisons.parseur_livraisons import Livraison
from backend.tournee.tournee import Tournee


@dataclass
class Coursier:
    """Un coursier de la planification.

    Pas frozen : Planification lui assigne des livraisons et recalcule sa
    tournée. C'est le coursier qui porte le lien vers ses livraisons, ce qui
    permet à Livraison de rester frozen : une livraison « sans coursier » est
    une livraison qui n'est dans la liste d'aucun coursier.

    Attributes:
        id: numéro unique du coursier.
        nom, prenom: identité du coursier (vides tant qu'on ne les a pas
            saisies).
        livraisons: livraisons assignées à ce coursier.
        tournee: tournée calculée pour ces livraisons ; None tant qu'aucune
            n'a été calculée.
    """

    id: int
    nom: str = ""
    prenom: str = ""
    livraisons: list[Livraison] = field(default_factory=list)
    tournee: Tournee | None = None
