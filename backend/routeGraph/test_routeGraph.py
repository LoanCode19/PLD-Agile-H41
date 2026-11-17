import os

import pytest

from backend.routeGraph.routeGraph import RouteGraph

RESSOURCES = os.path.join(os.path.dirname(__file__), "..", "..", "ressources")

XML_MINI = """<reseau>
  <noeud id="1" latitude="45.0" longitude="4.0"/>
  <noeud id="2" latitude="45.1" longitude="4.1"/>
  <troncon origine="1" destination="2" longueur="123.5" nomRue="Rue A"/>
</reseau>"""


def load(tmp_path, content):
    p = tmp_path / "plan.xml"
    p.write_text(content, encoding="utf-8")
    g = RouteGraph()
    g.construct_from_xml(str(p))
    return g


def test_parse_mini_plan(tmp_path):
    g = load(tmp_path, XML_MINI)
    assert g.node_count == 2 and g.edge_count == 1
    assert g.nodes["1"].latitude == 45.0
    edge = g.get_connections("1")[0]
    assert (edge.destination, edge.length, edge.street_name) == ("2", 123.5, "Rue A")
    # tronçon orienté : pas de retour 2 -> 1
    assert g.get_connections("2") == []


def test_edge_to_unknown_node(tmp_path):
    with pytest.raises(KeyError):
        load(tmp_path, XML_MINI.replace('destination="2"', 'destination="99"'))


@pytest.mark.parametrize("name", ["petitPlan.xml", "moyenPlan.xml", "grandPlan.xml"])
def test_real_plans(name):
    g = RouteGraph()
    g.construct_from_xml(os.path.join(RESSOURCES, name))
    assert g.node_count > 0 and g.edge_count > 0
