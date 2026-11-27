"""Erreurs metier du backend.

Une ``ErreurMetier`` est une erreur *prevue* : elle vient de l'utilisateur
(fichier invalide, actions dans le mauvais ordre...) et son message peut
etre affiche tel quel dans l'interface.

Le code metier leve ces erreurs sans rien savoir de HTTP. C'est ``api.py``
qui les transforme en reponse JSON, au format :

    {"erreur": {"code": "FICHIER_INVALIDE", "message": "...", "details": {...}}}

- ``code`` : identifiant stable, que le frontend peut tester ;
- ``message`` : texte lisible, destine a l'utilisateur ;
- ``details`` : donnees complementaires (ex : adresses inconnues).

Une erreur qui n'est PAS une ``ErreurMetier`` (TypeError, KeyError...) est
un bug : elle donne une erreur 500, sans etre deguisee en "fichier invalide".

Regle pour ajouter une classe : une classe par *reaction differente*
attendue cote frontend, pas une classe par message.
"""


class ErreurMetier(Exception):
    """Classe de base des erreurs prevues, affichables a l'utilisateur."""

    code = "ERREUR_METIER"
    status = 400  # code HTTP renvoye par l'API

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# --- Fichiers uploades -------------------------------------------------------

class FichierInvalide(ErreurMetier):
    """Un fichier uploade est illisible ou ne respecte pas le format."""

    code = "FICHIER_INVALIDE"


class FichierCarteInvalide(FichierInvalide):
    """Le fichier de carte (plan) est invalide."""

    code = "CARTE_INVALIDE"


class FichierLivraisonsInvalide(FichierInvalide):
    """Le fichier de demandes de livraisons est invalide."""

    code = "LIVRAISONS_INVALIDES"


class AdressesInconnues(ErreurMetier):
    """Des adresses de la demande n'existent pas sur la carte chargee."""

    code = "ADRESSES_INCONNUES"

    def __init__(self, adresses: list[int]):
        super().__init__(
            f"Adresses absentes de la carte : {adresses[:5]}"
            f"{' ...' if len(adresses) > 5 else ''} (mauvaise carte ?)",
            details={"adresses": adresses},
        )


# --- Etat de l'application ---------------------------------------------------

class DonneesManquantes(ErreurMetier):
    """Une action demande des donnees qui n'ont pas encore ete chargees."""

    code = "DONNEES_MANQUANTES"
    status = 409  # Conflict : la requete est valide, mais pas dans cet etat


class CarteNonChargee(DonneesManquantes):
    code = "CARTE_NON_CHARGEE"

    def __init__(self):
        super().__init__("Aucune carte chargée : uploadez d'abord une carte")


class LivraisonsNonChargees(DonneesManquantes):
    code = "LIVRAISONS_NON_CHARGEES"

    def __init__(self):
        super().__init__(
            "Aucune livraison chargée : uploadez d'abord les livraisons"
        )


class AucuneLivraisonAssignee(DonneesManquantes):
    """On demande la tournee d'un coursier a qui rien n'a ete assigne."""

    code = "AUCUNE_LIVRAISON_ASSIGNEE"

    def __init__(self, id_coursier: int):
        super().__init__(
            f"Aucune livraison assignée au coursier {id_coursier}",
            details={"coursier": id_coursier},
        )


# --- Ressources introuvables -------------------------------------------------

class CoursierInconnu(ErreurMetier):
    code = "COURSIER_INCONNU"
    status = 404

    def __init__(self, id_coursier: int):
        super().__init__(
            f"Aucun coursier avec l'id {id_coursier}",
            details={"coursier": id_coursier},
        )


class LivraisonsInconnues(ErreurMetier):
    code = "LIVRAISONS_INCONNUES"
    status = 404

    def __init__(self, ids: list[int]):
        super().__init__(
            f"Aucune livraison avec l'id {ids}", details={"livraisons": ids}
        )


# --- Calcul ------------------------------------------------------------------

class TourneeImpossible(ErreurMetier):
    """Les donnees sont valides mais aucune tournee ne peut etre calculee."""

    code = "TOURNEE_IMPOSSIBLE"
    status = 422  # Unprocessable : donnees comprises mais non traitables
