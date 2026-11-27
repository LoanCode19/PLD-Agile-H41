import xml.etree.ElementTree as ET
from dataclasses import dataclass

from erreurs import FichierCarteInvalide


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
        """Remplit le graphe depuis un fichier XML de plan.

        Raises:
            FichierCarteInvalide: fichier illisible, XML mal forme, attribut
                manquant ou invalide, troncon vers un noeud inconnu, ou
                aucune intersection.
        """
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as e:
            raise FichierCarteInvalide(f"XML mal formé : {e}") from e
        except OSError as e:
            raise FichierCarteInvalide(f"Lecture impossible du fichier : {e}") from e

        # `contexte` situe l'erreur dans le fichier pour le message affiché
        # à l'utilisateur (ex : "Noeud 12 : attribut 'latitude' manquant").
        for index, node in enumerate(root.findall('noeud'), start=1):
            contexte = f"Noeud {index}"
            self.add_node(
                _attribut(node, 'id', int, contexte),
                _attribut(node, 'latitude', float, contexte),
                _attribut(node, 'longitude', float, contexte),
            )
        # XML valide mais sans aucun <noeud> : typiquement un fichier de
        # livraisons uploadé à la place de la carte.
        if not self.nodes:
            raise FichierCarteInvalide(
                "Ce n'est pas une carte : aucune intersection <noeud> trouvée"
            )

        for index, edge in enumerate(root.findall('troncon'), start=1):
            contexte = f"Tronçon {index}"
            origin = _attribut(edge, 'origine', int, contexte)
            destination = _attribut(edge, 'destination', int, contexte)
            length = _attribut(edge, 'longueur', float, contexte)
            # add_edge lève KeyError si le tronçon cite un noeud absent.
            # Ici ce noeud vient du fichier : c'est le fichier qui est
            # invalide, pas un bug, d'où la conversion en FichierCarteInvalide.
            try:
                self.add_edge(origin, destination, length, edge.get('nomRue', ""))
            except KeyError as e:
                raise FichierCarteInvalide(f"{contexte} : {e.args[0]}") from e


def _attribut(element: ET.Element, nom: str, convertir, contexte: str):
    """Lit un attribut obligatoire et le convertit (int, float...)."""
    valeur = element.get(nom)
    if valeur is None:
        raise FichierCarteInvalide(f"{contexte} : attribut '{nom}' manquant")
    try:
        return convertir(valeur)
    except ValueError:
        raise FichierCarteInvalide(
            f"{contexte} : '{nom}' invalide, reçu '{valeur}'"
        ) from None
