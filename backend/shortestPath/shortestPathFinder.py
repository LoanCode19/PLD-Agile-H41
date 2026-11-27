import heapq
import math

from erreurs import AdressesInconnues, TourneeImpossible
from livraisons.parseur_livraisons import DemandeLivraisons, Livraison
from routeGraph.routeGraph import Edge, RouteGraph
from tournee.tournee import Passage, Tournee, TypeArret

VITESSE_LIVREUR = 15 / 3.6  # 15 km/h, en m/s (pour les horaires)
HEURE_MAX_RETOUR = 13 * 3600  # 13h00, en secondes après minuit
Etat = tuple[int, int]  # (masque des arrêts visités, dernier arrêt)


class ShortestPathFinder:
    def __init__(
        self,
        graph: RouteGraph,
        demande: DemandeLivraisons,
        livraisons: list[Livraison] | None = None,
    ):
        """
        Args:
            demande: donne l'entrepôt et l'heure de départ.
            livraisons: les livraisons à faire (celles d'un coursier) ;
                si None, toutes celles de la demande.
        """
        self.graph = graph
        self.demande_livraisons = demande
        self.livraisons: list[Livraison] = list(
            demande.livraisons if livraisons is None else livraisons
        )
        self.adresse_entrepot: int = demande.adresse_entrepot
        #   0      entrepôt
        #   2i + 1 enlèvement de la livraison i
        #   2i + 2 livraison de la livraison i
        self.arrets: list[int] = [self.adresse_entrepot]
        for livraison in self.livraisons:
            self.arrets.append(livraison.adresse_enlevement)
            self.arrets.append(livraison.adresse_livraison)

        inconnues = [a for a in self.arrets if a not in graph]
        if inconnues:
            # Déjà vérifié au chargement (Planification.charger_demandes) ;
            # gardé comme filet de sécurité quand la classe est utilisée seule.
            raise AdressesInconnues(inconnues)

        adresses = set(self.arrets)

        # distances[a][b] = plus courte distance (m) de l'adresse a à
        # l'adresse b.
        self.distances: dict[int, dict[int, float]] = {
            adresse: {} for adresse in adresses
        }

        # predecesseurs[source][noeud] = tronçon qui mène à noeud sur le plus
        # court chemin depuis source (pour reconstruire les trajets).
        self.predecesseurs: dict[int, dict[int, Edge]] = {
            adresse: {} for adresse in adresses
        }

        for adresse in adresses:
            self._dijkstra(adresse, adresses)

    def calculer_tournee(self) -> Tournee:
        """Nœuds du graphe à parcourir, de l'entrepôt à l'entrepôt.

        Chaque nœud est un Passage : les arrêts (entrepôt, enlèvement,
        livraison) portent leurs horaires et leur livraison, les simples
        passages non. Une tournée qui rentre après HEURE_MAX_RETOUR est quand
        même renvoyée, avec depasse_heure_max = True.
        """
        ordre, horaires = self.held_karp()
        chemin = [self._passage_arret(ordre[0], horaires[0])]
        depasse_heure_max = horaires[-1][0] > HEURE_MAX_RETOUR
        for k in range(1, len(ordre)):
            depart = self.arrets[ordre[k - 1]]
            arrivee = self.arrets[ordre[k]]
            for noeud in self._noeuds_entre(depart, arrivee):
                chemin.append(self._passage(noeud, TypeArret.PASSAGE))  # simple passage
            chemin.append(self._passage_arret(ordre[k], horaires[k]))
        return Tournee(chemin, depasse_heure_max)

    def _dijkstra(self, source: int, cibles: set[int]) -> None:
        """Remplit distances[source] et predecesseurs[source].

        Poids d'un tronçon = sa longueur (m).
        """

        def relacher(troncon: Edge, distance_origine: float) -> None:
            """Si passer par ce tronçon raccourcit le trajet jusqu'à sa
            destination, on retient la nouvelle distance et ce tronçon."""
            nouvelle = distance_origine + troncon.length
            if nouvelle < distance.get(troncon.destination, math.inf):
                distance[troncon.destination] = nouvelle
                predecesseurs[troncon.destination] = troncon
                heapq.heappush(tas, (nouvelle, troncon.destination))

        distance = {source: 0.0}
        predecesseurs = self.predecesseurs[source]
        restantes = set(cibles)
        visited = set()
        tas = [(0.0, source)]

        while tas and restantes:
            d, noeud = heapq.heappop(tas)
            if noeud in visited:
                continue  # entrée périmée : déjà atteint par un chemin plus court
            visited.add(noeud)
            restantes.discard(noeud)
            for troncon in self.graph.get_connections(noeud):
                relacher(troncon, d)
        self.distances[source] = {c: distance[c] for c in cibles if c in visited}

    def _noeuds_entre(self, depart: int, arrivee: int) -> list[int]:
        """Nœuds traversés entre depart et arrivee (tous deux exclus)."""
        noeuds = []
        if depart == arrivee:
            return noeuds
        predecesseurs = self.predecesseurs[depart]
        noeud = predecesseurs[arrivee].origin
        while noeud != depart:
            noeuds.append(noeud)
            noeud = predecesseurs[noeud].origin
        noeuds.reverse()
        return noeuds

    def held_karp(self) -> tuple[list[int], list[tuple[float, float]]]:
        """Ordre de passage optimal (indices d'arrêts, de 0 à 0) et les
        horaires (arrivée, départ) de chaque arrêt de l'ordre, en secondes
        après minuit.

        couche[état] = plus courte distance depuis l'entrepôt pour atteindre
        cet état ; parent[état] = état d'avant.
        """
        n = len(self.arrets)
        D = self._matrice_distances()
        if n == 1:
            return [0, 0], self._horaires([0, 0], D)

        couche, parent = self._etats_de_depart(D)
        for _ in range(n - 2):
            couche = self._couche_suivante(couche, parent, D)

        etat_final = self._meilleur_retour(couche, D)
        ordre = self._reconstruire_ordre(etat_final, parent)
        horaires = self._horaires(ordre, D)
        return (
            ordre,
            horaires,
        )  # horraires = [(arrivée, départ) de chaque arrêt de l'ordre,
        # en secondes après minuit, horaires[-1][0] pour l'heure de fin]

    def _matrice_distances(self) -> list[list[float]]:
        """D[i][j] = distance (m) de l'arrêt i à l'arrêt j."""
        return [
            [self.distances[a].get(b, math.inf) for b in self.arrets]
            for a in self.arrets
        ]

    @staticmethod
    def _bit(arret: int) -> int:
        """Bit de l'arrêt dans le masque (l'entrepôt n'en a pas)."""
        return 1 << (arret - 1)

    def _peut_visiter(self, masque: int, arret: int) -> bool:
        """Pas encore visité et, si c'est une livraison, colis déjà enlevé."""
        if masque & self._bit(arret):
            return False  # déjà visité
        est_livraison = arret % 2 == 0
        if est_livraison:
            enlevement = arret - 1
            return bool(
                masque & self._bit(enlevement)
            )  # On peut si on a recup le colis
        return True  # si c'est une recup de colis, on peut tt le temps

    def _etats_de_depart(
        self, D: list[list[float]]
    ) -> tuple[dict[Etat, float], dict[Etat, Etat | None]]:
        """Un seul arrêt visité : forcément un enlèvement (indice impair)."""
        couche: dict[Etat, float] = {}  # états avec un arrêt visité
        parent: dict[
            Etat, Etat | None
        ] = {}  # parent de chaque état (None pour les états de départ)
        for enlevement in range(
            1, len(self.arrets), 2
        ):  # tous les enlèvements initiaux possibles (cf indiçage tableau)
            etat = (self._bit(enlevement), enlevement)  #:masque de l'état maj
            couche[etat] = D[0][
                enlevement
            ]  # distance optimale pour arriver dans cet état
            parent[etat] = None
        return couche, parent

    def _couche_suivante(
        self,
        couche: dict[Etat, float],
        parent: dict[Etat, Etat | None],
        D: list[list[float]],
    ) -> dict[Etat, float]:
        """États avec un arrêt visité de plus. Complète parent au passage."""
        suivante: dict[Etat, float] = {}
        for (masque, dernier), distance in couche.items():
            for arret in range(1, len(self.arrets)):
                if not self._peut_visiter(masque, arret):
                    continue
                etat = (masque | self._bit(arret), arret)
                nouvelle = distance + D[dernier][arret]
                if nouvelle < suivante.get(etat, math.inf):
                    suivante[etat] = nouvelle
                    parent[etat] = (masque, dernier)
        return suivante

    def _meilleur_retour(self, couche: dict[Etat, float], D: list[list[float]]) -> Etat:
        """État final qui minimise la distance, retour à l'entrepôt compris."""
        meilleur_etat = None
        meilleure_distance = math.inf
        for etat, distance in couche.items():
            _, dernier = etat
            totale = distance + D[dernier][0]
            if totale < meilleure_distance:
                meilleur_etat = etat
                meilleure_distance = totale
        if meilleur_etat is None:
            raise TourneeImpossible(
                "Aucune tournée possible : certains arrêts sont inaccessibles "
                "depuis l'entrepôt (ou ne permettent pas d'y revenir)"
            )
        return meilleur_etat

    def _reconstruire_ordre(
        self, etat_final: Etat, parent: dict[Etat, Etat | None]
    ) -> list[int]:
        """Ordre des arrêts (indices) pour atteindre l'état final."""
        ordre = []
        etat = etat_final
        while etat is not None:
            _, dernier = etat
            ordre.append(dernier)
            etat = parent[etat]
        ordre.append(0)  # départ de l'entrepôt
        ordre.reverse()
        ordre.append(0)  # retour à l'entrepôt
        return ordre

    def _horaires(
        self, ordre: list[int], D: list[list[float]]
    ) -> list[tuple[float, float]]:
        """(heure d'arrivée, heure de départ) de chaque arrêt de l'ordre."""
        heure = float(self.demande_livraisons.heure_depart)
        horaires = [(heure, heure)]  # départ de l'entrepôt
        for k in range(1, len(ordre)):
            precedent = ordre[k - 1]
            arret = ordre[k]
            arrivee = heure + D[precedent][arret] / VITESSE_LIVREUR
            heure = arrivee + self._duree_service(arret)
            horaires.append((arrivee, heure))
        return horaires

    def _duree_service(self, arret: int) -> int:
        """Durée (s) passée sur place à cet arrêt."""
        if arret == 0:
            return 0  # entrepôt
        livraison = self.livraisons[(arret - 1) // 2]
        est_enlevement = arret % 2 == 1
        if est_enlevement:
            return livraison.duree_enlevement
        return livraison.duree_livraison

    def _passage_arret(self, arret: int, horaire: tuple[float, float]) -> Passage:
        """Passage à l'arrêt d'indice arret, avec ses horaires (arrivée, départ)."""
        if arret == 0:
            return self._passage(
                self.adresse_entrepot, TypeArret.ENTREPOT, None, horaire
            )
        livraison = self.livraisons[(arret - 1) // 2]
        est_enlevement = arret % 2 == 1
        type = TypeArret.ENLEVEMENT if est_enlevement else TypeArret.LIVRAISON
        return self._passage(self.arrets[arret], type, livraison, horaire)

    def _passage(
        self,
        adresse: int,
        type: TypeArret,
        livraison: Livraison | None = None,
        horaire: tuple[float, float] | tuple[None, None] = (None, None),
    ) -> Passage:
        """Passage par le nœud adresse (coordonnées lues dans le graphe)."""
        noeud = self.graph.nodes[adresse]
        heure_arrivee, heure_depart = horaire
        return Passage(
            adresse=adresse,
            latitude=noeud.latitude,
            longitude=noeud.longitude,
            type=type,
            livraison=livraison,
            heure_arrivee=heure_arrivee,
            heure_depart=heure_depart,
        )
