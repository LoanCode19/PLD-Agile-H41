"""Tests de Planification."""

from pathlib import Path

import pytest

from coursier.coursier import Coursier
from planification.planification import Planification
from routeGraph.routeGraph import RouteGraph


def avec_un_coursier(planification: Planification) -> Coursier:
    """Crée le coursier 1 (une planification démarre sans coursier)."""
    planification.coursiers[1] = Coursier(1)
    return planification.coursiers[1]


def carte() -> RouteGraph:
    """Triangle 1-2-3, double sens, 100 m par tronçon."""
    g = RouteGraph()
    for noeud in (1, 2, 3):
        g.add_node(noeud, 45.0, 4.0)
    for a, b in ((1, 2), (2, 3), (3, 1)):
        g.add_edge(a, b, 100)
        g.add_edge(b, a, 100)
    return g


def fichier_demandes(tmp_path: Path) -> Path:
    """Entrepôt en 1, une livraison de 2 vers 3."""
    chemin = tmp_path / "demandes.xml"
    chemin.write_text(
        '<demandeDeLivraisons><entrepot adresse="1" heureDepart="08:00"/>'
        '<livraison adresseEnlevement="2" adresseLivraison="3"'
        ' dureeEnlevement="60" dureeLivraison="60"/></demandeDeLivraisons>',
        encoding="utf-8",
    )
    return chemin


def test_charger_demandes_efface_livraisons_et_tournee_des_coursiers(tmp_path):
    planification = Planification(carte())
    demande = planification.charger_demandes(fichier_demandes(tmp_path))
    coursier = avec_un_coursier(planification)
    coursier.livraisons = list(demande.livraisons)
    planification.calculer_tournee(1)

    nouvelle = planification.charger_demandes(fichier_demandes(tmp_path))
    assert planification.demande is nouvelle
    assert coursier.livraisons == []
    assert coursier.tournee is None


def test_calculer_tournee_sur_les_livraisons_du_coursier(tmp_path):
    planification = Planification(carte())
    demande = planification.charger_demandes(fichier_demandes(tmp_path))
    avec_un_coursier(planification).livraisons = list(demande.livraisons)
    tournee = planification.calculer_tournee(1)
    assert planification.coursiers[1].tournee is tournee
    assert [arret.adresse for arret in tournee.arrets] == [1, 2, 3, 1]


def test_calculer_tournee_sans_livraison_assignee(tmp_path):
    planification = Planification(carte())
    planification.charger_demandes(fichier_demandes(tmp_path))
    avec_un_coursier(planification)
    with pytest.raises(ValueError, match="Aucune livraison assignée"):
        planification.calculer_tournee(1)


def test_calculer_tournee_sans_demande():
    with pytest.raises(ValueError, match="Aucune demande"):
        planification = Planification(carte())
        avec_un_coursier(planification)
        planification.calculer_tournee(1)


def test_nouvelle_planification_sans_coursier():
    assert Planification(carte()).coursiers == {}
