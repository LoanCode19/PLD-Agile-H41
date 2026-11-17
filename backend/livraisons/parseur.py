"""Chargement du fichier XML des livraisons a faire.

On utilise ``xml.etree.ElementTree`` de la bibliotheque standard :
aucune dependance externe, suffisant pour des fichiers de cette taille.

Format attendu (voir le README) :

    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <demandeDeLivraisons>
        <entrepot adresse="25327124" heureDepart="08:00"/>
        <livraison adresseEnlevement="26464256" adresseLivraison="239603465"
                   dureeEnlevement="0" dureeLivraison="600"/>
    </demandeDeLivraisons>

Toute erreur de format leve une :class:`FichierLivraisonsInvalide`
avec un message lisible, que l'appelant peut transmettre tel quel au front.
"""

import re
import xml.etree.ElementTree as ET
from datetime import time
from pathlib import Path

from .modeles import DemandeLivraisons, Livraison

RACINE_ATTENDEUE = "demandeDeLivraisons"
FORMAT_HEURE = "HH:MM"


class FichierLivraisonsInvalide(Exception):
    """Le fichier XML ne respecte pas le format attendu."""


def _attribut(element: ET.Element, nom: str, contexte: str) -> str:
    """Renvoie un attribut obligatoire, ou leve une erreur claire."""
    valeur = element.get(nom)
    if valeur is None:
        raise FichierLivraisonsInvalide(
            f"{contexte} : attribut '{nom}' manquant"
        )
    return valeur


def _entier(valeur: str, nom: str, contexte: str) -> int:
    """Convertit un attribut en entier positif ou nul."""
    try:
        nombre = int(valeur)
    except ValueError:
        raise FichierLivraisonsInvalide(
            f"{contexte} : '{nom}' doit etre un entier, recu '{valeur}'"
        ) from None
    if nombre < 0:
        raise FichierLivraisonsInvalide(
            f"{contexte} : '{nom}' doit etre positif, recu {nombre}"
        )
    return nombre


def _heure(valeur: str, contexte: str) -> time:
    """Convertit une heure au format HH:MM."""
    if not re.fullmatch(r"\d{2}:\d{2}", valeur):
        raise FichierLivraisonsInvalide(
            f"{contexte} : 'heureDepart' doit etre une heure au format "
            f"{FORMAT_HEURE}, recu '{valeur}'"
        )
    try:
        return time.fromisoformat(valeur)
    except ValueError:
        raise FichierLivraisonsInvalide(
            f"{contexte} : 'heureDepart' n'est pas une heure valide, "
            f"recu '{valeur}'"
        ) from None


def charger_livraisons(chemin: str | Path) -> DemandeLivraisons:
    """Charge et valide un fichier XML de demandes de livraisons.

    Args:
        chemin: chemin vers le fichier XML.

    Returns:
        La demande de livraisons prete a l'emploi.

    Raises:
        FichierLivraisonsInvalide: fichier introuvable, XML mal forme,
            ou contenu non conforme au format attendu.
    """
    chemin = Path(chemin)
    try:
        racine = ET.parse(chemin).getroot()
    except ET.ParseError as e:
        raise FichierLivraisonsInvalide(f"XML mal forme : {e}") from e
    except OSError as e:
        raise FichierLivraisonsInvalide(
            f"Lecture impossible du fichier '{chemin}' : {e}"
        ) from e

    if racine.tag != RACINE_ATTENDEUE:
        raise FichierLivraisonsInvalide(
            f"Racine attendue '<{RACINE_ATTENDEUE}>', "
            f"recue '<{racine.tag}>'"
        )

    entrepot = racine.find("entrepot")
    if entrepot is None:
        raise FichierLivraisonsInvalide("Element <entrepot> manquant")
    contexte_entrepot = "Element <entrepot>"
    adresse_entrepot = _entier(
        _attribut(entrepot, "adresse", contexte_entrepot),
        "adresse",
        contexte_entrepot,
    )
    heure_depart = _heure(
        _attribut(entrepot, "heureDepart", contexte_entrepot),
        contexte_entrepot,
    )

    livraisons = []
    for index, element in enumerate(racine.findall("livraison"), start=1):
        contexte = f"Livraison {index}"
        livraisons.append(
            Livraison(
                adresse_enlevement=_entier(
                    _attribut(element, "adresseEnlevement", contexte),
                    "adresseEnlevement",
                    contexte,
                ),
                adresse_livraison=_entier(
                    _attribut(element, "adresseLivraison", contexte),
                    "adresseLivraison",
                    contexte,
                ),
                duree_enlevement=_entier(
                    _attribut(element, "dureeEnlevement", contexte),
                    "dureeEnlevement",
                    contexte,
                ),
                duree_livraison=_entier(
                    _attribut(element, "dureeLivraison", contexte),
                    "dureeLivraison",
                    contexte,
                ),
            )
        )

    return DemandeLivraisons(
        adresse_entrepot=adresse_entrepot,
        heure_depart=heure_depart,
        livraisons=tuple(livraisons),
    )
