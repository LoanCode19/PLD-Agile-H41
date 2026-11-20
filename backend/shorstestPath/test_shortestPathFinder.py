"""Tests de ShortestPathFinder.

Depuis la racine du dépôt (-s pour voir les temps affichés) :
    python -m pytest backend/shorstestPath -s
"""

import functools
import math
import re
import time
from pathlib import Path

import pytest

from backend.livraisons.parseur_livraisons import (
    DemandeLivraisons,
    Livraison,
    charger_livraisons,
)
from backend.routeGraph.routeGraph import RouteGraph
from backend.shorstestPath.shortestPathFinder import (
    HEURE_MAX_RETOUR,
    VITESSE_LIVREUR,
    ShortestPathFinder,
)

RESSOURCES = Path(__file__).resolve().parents[2] / "ressources"
HEURE_DEPART = 8 * 3600
LIMITE_PERF_S = 3.0


# Outils


def hms(secondes: float) -> str:
    s = int(round(secondes))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def graphe(troncons: list[tuple[int, int, float]]) -> RouteGraph:
    """Graphe construit à partir de (origine, destination, longueur)."""
    g = RouteGraph()
    for origine, destination, _ in troncons:
        for noeud in (origine, destination):
            if noeud not in g:
                g.add_node(noeud, 45.0, 4.0)
    for origine, destination, longueur in troncons:
        g.add_edge(origine, destination, longueur)
    return g


@functools.cache
def charger_plan(nom: str) -> RouteGraph:
    g = RouteGraph()
    g.construct_from_xml(RESSOURCES / nom)
    return g


def charger_demande(nom: str, tmp_path: Path) -> DemandeLivraisons:
    """Les fichiers fournis ont heureDepart="8:0:0", que le parseur n'accepte
    pas (il attend HH:MM) : on charge une copie avec "08:00"."""
    texte = (RESSOURCES / nom).read_text(encoding="utf-8")
    texte = re.sub(
        r'heureDepart="(\d+):(\d+):\d+"',
        lambda m: f'heureDepart="{int(m[1]):02d}:{int(m[2]):02d}"',
        texte,
    )
    copie = tmp_path / nom
    copie.write_text(texte, encoding="utf-8")
    return charger_livraisons(copie)


def ordres_valides(restants: frozenset[int], faits: tuple[int, ...] = ()):
    """Tous les ordres où chaque livraison (indice pair) suit son enlèvement."""
    if not restants:
        yield faits
        return
    for arret in restants:
        est_livraison = arret % 2 == 0
        if est_livraison and arret - 1 not in faits:
            continue
        yield from ordres_valides(restants - {arret}, faits + (arret,))


def heure_retour_force_brute(finder: ShortestPathFinder) -> float:
    """Heure de retour la plus tôt, en essayant tous les ordres valides."""
    demande = finder.demande_livraisons
    D = finder._matrice_distances()
    services = [0]
    for livraison in demande.livraisons:
        services += [livraison.duree_enlevement, livraison.duree_livraison]

    meilleure = math.inf
    for ordre in ordres_valides(frozenset(range(1, len(finder.arrets)))):
        heure = demande.heure_depart
        precedent = 0
        for arret in ordre:
            heure += D[precedent][arret] / VITESSE_LIVREUR + services[arret]
            precedent = arret
        heure += D[precedent][0] / VITESSE_LIVREUR
        meilleure = min(meilleure, heure)
    return meilleure


# Données

# Ville de 8 intersections, avec des sens uniques. Entrepôt en 1.
GRAPHE = graphe(
    [
        (1, 2, 300),
        (2, 1, 300),
        (2, 3, 200),
        (3, 4, 400),
        (4, 5, 250),
        (5, 6, 300),
        (6, 7, 150),
        (7, 8, 350),
        (8, 1, 200),
        (3, 7, 500),
        (7, 3, 500),
        (5, 1, 600),
        (4, 8, 450),
        (6, 2, 700),
    ]
)

CAS = {
    "une livraison": (Livraison(3, 6, 60, 120),),
    "adresses partagées": (
        Livraison(2, 5, 60, 120),  # livre en 5...
        Livraison(5, 1, 30, 90),  # ...où on enlève, pour livrer à l'entrepôt
        Livraison(1, 7, 45, 75),  # enlèvement à l'entrepôt
    ),
    "enlèvement et livraison au même endroit": (
        Livraison(4, 4, 60, 120),
        Livraison(6, 3, 30, 90),
    ),
    "cinq livraisons": (
        Livraison(2, 7, 120, 300),
        Livraison(8, 3, 60, 240),
        Livraison(5, 2, 0, 600),
        Livraison(6, 4, 180, 60),
        Livraison(3, 8, 240, 120),
    ),
}

PETITS_FICHIERS = [
    ("petitPlan.xml", "demandePetit1.xml"),
    ("petitPlan.xml", "demandePetit2.xml"),
    ("moyenPlan.xml", "demandeMoyen3.xml"),
    ("moyenPlan.xml", "demandeMoyen5.xml"),
]
GROS_FICHIERS = [
    ("grandPlan.xml", "demandeGrand7.xml"),
    ("grandPlan.xml", "demandeGrand9.xml"),
    ("grandPlan.xml", "myDeliverRequest.xml"),
]


# Tests


@pytest.mark.parametrize("livraisons", CAS.values(), ids=CAS.keys())
def test_held_karp_contre_force_brute(livraisons):
    finder = ShortestPathFinder(GRAPHE, DemandeLivraisons(1, HEURE_DEPART, livraisons))

    debut = time.perf_counter()
    _, horaires = finder.held_karp()
    duree_hk = time.perf_counter() - debut

    debut = time.perf_counter()
    attendu = heure_retour_force_brute(finder)
    duree_fb = time.perf_counter() - debut

    print(
        f"\n{len(livraisons)} livraison(s) : retour {hms(horaires[-1][0])} "
        f"| held-karp {duree_hk * 1000:.1f} ms | force brute {duree_fb * 1000:.1f} ms"
    )
    assert horaires[-1][0] == pytest.approx(attendu)


@pytest.mark.parametrize("plan, nom_demande", PETITS_FICHIERS)
def test_petits_fichiers_contre_force_brute(plan, nom_demande, tmp_path):
    finder = ShortestPathFinder(
        charger_plan(plan), charger_demande(nom_demande, tmp_path)
    )
    route = finder.getBestRoute()
    attendu = heure_retour_force_brute(finder)
    print(f"\n{nom_demande} : retour {hms(route[-1][1])} (attendu {hms(attendu)})")
    assert route[-1][1] == pytest.approx(attendu)


@pytest.mark.parametrize("plan, nom_demande", GROS_FICHIERS)
def test_perf_gros_fichiers(plan, nom_demande, tmp_path):
    g = charger_plan(plan)
    demande = charger_demande(nom_demande, tmp_path)

    debut = time.perf_counter()
    route = ShortestPathFinder(g, demande).getBestRoute()
    duree = time.perf_counter() - debut

    print(f"\n{nom_demande} : retour {hms(route[-1][1])} | calcul {duree:.2f} s")
    assert route[-1][0] == demande.adresse_entrepot
    assert duree < LIMITE_PERF_S


def test_sans_livraison():
    route = ShortestPathFinder(
        GRAPHE, DemandeLivraisons(1, HEURE_DEPART, ())
    ).getBestRoute()
    assert route == [(1, HEURE_DEPART), (1, HEURE_DEPART)]


def test_arret_inaccessible():
    g = graphe([(1, 2, 100), (2, 1, 100)])
    g.add_node(3, 45.0, 4.0)  # aucun tronçon n'y mène
    demande = DemandeLivraisons(1, HEURE_DEPART, (Livraison(2, 3, 0, 0),))
    with pytest.raises(ValueError):
        ShortestPathFinder(g, demande).getBestRoute()


def test_retour_apres_heure_max():
    trop_long = HEURE_MAX_RETOUR - HEURE_DEPART + 1  # rien que sur place
    demande = DemandeLivraisons(1, HEURE_DEPART, (Livraison(3, 6, 0, trop_long),))
    with pytest.raises(ValueError):
        ShortestPathFinder(GRAPHE, demande).getBestRoute()
