import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Node:
    """Une intersection."""
    id: int
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class Edge:
    """Un tronçon orienté origin -> destination (longueur en mètres)."""
    origin: int
    destination: int
    length: float
    street_name: str = ""


class RouteGraph:
    def __init__(self):
        self.nodes = {}      # id -> Node
        self.adjacency = {}  # id -> liste de Edge sortants

    def add_node(self, node_id, latitude, longitude):
        self.nodes[node_id] = Node(node_id, latitude, longitude)
        self.adjacency.setdefault(node_id, [])

    def add_edge(self, origin, destination, length, street_name=""):
        """Ajoute un tronçon orienté origin -> destination."""
        if origin not in self.nodes or destination not in self.nodes:
            raise KeyError(f"Noeud inconnu dans le tronçon {origin} -> {destination}")
        self.adjacency[origin].append(Edge(origin, destination, length, street_name))

    def __contains__(self, node_id):
        return node_id in self.nodes

    @property
    def node_count(self):
        return len(self.nodes)

    @property
    def edge_count(self):
        return sum(len(edges) for edges in self.adjacency.values())

    def get_connections(self, node_id):
        """Liste des Edge sortant de node_id."""
        return self.adjacency.get(node_id, [])

    def construct_from_xml(self, xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for node in root.findall('noeud'):
            node_id = int(node.get('id'))
            latitude = float(node.get('latitude'))
            longitude = float(node.get('longitude'))
            self.add_node(node_id, latitude, longitude)
        for edge in root.findall('troncon'):
            origin = int(edge.get('origine'))
            destination = int(edge.get('destination'))
            length = float(edge.get('longueur'))
            street_name = edge.get('nomRue', "")
            self.add_edge(origin, destination, length, street_name)
