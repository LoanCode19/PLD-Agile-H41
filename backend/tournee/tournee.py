"""Résultat du calcul d'une tournée : le chemin suivi par un coursier.

Ce module ne dépend que de ``Livraison`` : ShortestPathFinder peut créer des
Tournee sans importer Planification (pas d'import circulaire).
"""

from dataclasses import dataclass
from enum import StrEnum

from livraisons.parseur_livraisons import Livraison


class TypeArret(StrEnum):
    """Ce que fait le coursier en passant par une intersection."""

    ENTREPOT = "entrepot"
    ENLEVEMENT = "enlevement"
    LIVRAISON = "livraison"
    PASSAGE = "passage"  # simple passage, sans s'arrêter


@dataclass(frozen=True)
class Passage:
    """Une intersection traversée par le coursier.

    Si le coursier s'y arrête (entrepôt, enlèvement, livraison), le passage
    porte ses horaires ; pour un simple passage, ils valent None.

    Attributes:
        adresse: id du Node traversé.
        latitude, longitude: copiées du Node, pour le tracé côté front.
        type: ce que fait le coursier à cette intersection.
        livraison: la livraison concernée (None pour l'entrepôt ou un
            simple passage).
        heure_arrivee: s après minuit (None pour un simple passage).
        heure_depart: s après minuit, = arrivée + durée d'enlèvement / de
            livraison (None pour un simple passage).
    """

    adresse: int
    latitude: float
    longitude: float
    type: TypeArret
    livraison: Livraison | None = None
    heure_arrivee: float | None = None
    heure_depart: float | None = None

    @property
    def est_arret(self) -> bool:
        return self.type is not TypeArret.PASSAGE


@dataclass
class Tournee:
    """Chemin d'un coursier, de l'entrepôt à l'entrepôt.

    Attributes:
        chemin: toutes les intersections traversées, dans l'ordre ; les
            arrêts sont les passages dont le type n'est pas PASSAGE.
        depasse_heure_max: True si le coursier rentre à l'entrepôt après
            l'heure limite (HEURE_MAX_RETOUR, 13h00). La tournée est quand
            même calculée : c'est à l'appelant de décider quoi en faire.
    """

    chemin: list[Passage]
    depasse_heure_max: bool

    @property
    def arrets(self) -> list[Passage]:
        """Passages où le coursier s'arrête (entrepôt, enlèvements, livraisons)."""
        return [passage for passage in self.chemin if passage.est_arret]

    @property
    def heure_retour(self) -> float:
        """Heure d'arrivée à l'entrepôt en fin de tournée (s après minuit)."""
        return self.chemin[-1].heure_arrivee
