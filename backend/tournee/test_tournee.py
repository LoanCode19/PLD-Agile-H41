"""Tests de Tournee et Passage."""

from livraisons.parseur_livraisons import Livraison
from tournee.tournee import Passage, Tournee, TypeArret

LIVRAISON = Livraison(1, 2, 3, 60, 120)


def tournee_exemple() -> Tournee:
    """Entrepôt 1 -> (passage 5) -> enlèvement 2 -> livraison 3 -> entrepôt 1."""
    return Tournee(
        chemin=[
            Passage(1, 45.0, 4.0, TypeArret.ENTREPOT, None, 28800, 28800),
            Passage(5, 45.0, 4.0, TypeArret.PASSAGE),
            Passage(2, 45.0, 4.0, TypeArret.ENLEVEMENT, LIVRAISON, 29000, 29060),
            Passage(3, 45.0, 4.0, TypeArret.LIVRAISON, LIVRAISON, 29200, 29320),
            Passage(1, 45.0, 4.0, TypeArret.ENTREPOT, None, 29500, 29500),
        ],
        depasse_heure_max=False,
    )


def test_un_simple_passage_n_est_pas_un_arret():
    assert not Passage(5, 45.0, 4.0, TypeArret.PASSAGE).est_arret
    assert Passage(1, 45.0, 4.0, TypeArret.ENTREPOT).est_arret


def test_arrets_ignore_les_simples_passages():
    adresses = [passage.adresse for passage in tournee_exemple().arrets]
    assert adresses == [1, 2, 3, 1]


def test_heure_retour_est_l_arrivee_a_l_entrepot():
    assert tournee_exemple().heure_retour == 29500


def test_type_arret_serialise_en_texte():
    assert TypeArret.PASSAGE == "passage"
