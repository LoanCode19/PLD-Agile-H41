"""Tests de Planification."""

from pathlib import Path

import pytest

from planification.planification import Planification
from routeGraph.routeGraph import RouteGraph


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


def test_charger_demandes_donne_les_livraisons_au_coursier(tmp_path):
    planification = Planification(carte())
    demande = planification.charger_demandes(fichier_demandes(tmp_path))
    assert planification.demande is demande
    assert planification.coursier.livraisons == list(demande.livraisons)
    assert planification.coursier.tournee is None


def test_calculer_tournee(tmp_path):
    planification = Planification(carte())
    planification.charger_demandes(fichier_demandes(tmp_path))
    tournee = planification.calculer_tournee()
    assert planification.coursier.tournee is tournee
    assert [arret.adresse for arret in tournee.arrets] == [1, 2, 3, 1]


def test_calculer_tournee_sans_demande():
    with pytest.raises(ValueError, match="Aucune demande"):
        Planification(carte()).calculer_tournee()
