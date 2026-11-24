"""Tests de Coursier."""

from coursier.coursier import Coursier
from livraisons.parseur_livraisons import Livraison


def test_nouveau_coursier_sans_livraison_ni_tournee():
    coursier = Coursier(1)
    assert coursier.livraisons == []
    assert coursier.tournee is None


def test_chaque_coursier_a_sa_propre_liste_de_livraisons():
    premier, second = Coursier(1), Coursier(2)
    premier.livraisons.append(Livraison(1, 2, 3, 60, 120))
    assert second.livraisons == []
