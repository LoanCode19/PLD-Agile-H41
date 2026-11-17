"""Modeles metier pour une demande de livraisons."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Livraison:
    """Une demande de livraison (enlevement + livraison).

    Les adresses sont des identifiants d'intersections de la carte.
    Les durees sont exprimees en secondes.
    """

    adresse_enlevement: int
    adresse_livraison: int
    duree_enlevement: int
    duree_livraison: int


@dataclass(frozen=True)
class DemandeLivraisons:
    """Une demande de livraisons chargee depuis le fichier XML.

    Attributes:
        adresse_entrepot: identifiant de l'intersection ou se trouve l'entrepot.
        heure_depart: heure de depart des coursiers, en secondes apres
            minuit (08:00 -> 28800).
        livraisons: tuple des demandes de livraison, dans l'ordre du fichier.
    """

    adresse_entrepot: int
    heure_depart: int
    livraisons: tuple[Livraison, ...]
