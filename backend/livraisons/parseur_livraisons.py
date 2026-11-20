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

L'attribut ``heureDepart`` de l'entrepot accepte deux formats :
``HH:MM`` (ex : ``08:00``) ou ``HH:MM:SS`` (ex : ``8:0:0``).

Toute erreur de format leve une :class:`FichierLivraisonsInvalide`
avec un message lisible, que l'appelant peut transmettre tel quel au front.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass



@dataclass(frozen=True)
class Livraison:
    """Une demande de livraison (enlevement + livraison).

    Les adresses sont des identifiants d'intersections de la carte.
    Les durees sont exprimees en secondes.
    """

    adresse_enlevement: int
    adresse_livraison: int
    duree_enlevement: int
    duree_livraison: int


@dataclass(frozen=True)
class DemandeLivraisons:
    """Une demande de livraisons chargee depuis le fichier XML.

    Attributes:
        adresse_entrepot: identifiant de l'intersection ou se trouve l'entrepot.
        heure_depart: heure de depart des coursiers, en secondes apres
            minuit (08:00 -> 28800).
        livraisons: tuple des demandes de livraison, dans l'ordre du fichier.
    """

    adresse_entrepot: int
    heure_depart: int
    livraisons: tuple[Livraison, ...]









RACINE_ATTENDEUE = "demandeDeLivraisons"

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


def _heure_en_secondes(valeur: str, contexte: str) -> int:
    """Convertit une heure 'HH:MM' ou 'HH:MM:SS' en secondes apres minuit."""
    champs = valeur.split(":")
    if len(champs) not in (2, 3) or not all(c.isdecimal() for c in champs):
        raise FichierLivraisonsInvalide(
            f"{contexte} : 'heureDepart' doit etre une heure au format "
            f"HH:MM ou HH:MM:SS, recu '{valeur}'"
        )
    heures, minutes = int(champs[0]), int(champs[1])
    secondes = int(champs[2]) if len(champs) == 3 else 0
    if heures > 23 or minutes > 59 or secondes > 59:
        raise FichierLivraisonsInvalide(
            f"{contexte} : 'heureDepart' n'est pas une heure valide, "
            f"recu '{valeur}'"
        )
    return heures * 3600 + minutes * 60 + secondes


def charger_livraisons(chemin: str | Path) -> DemandeLivraisons:
    """Charge et valide un fichier XML de demandes de livraisons.

    Args:
        chemin: chemin vers le fichier XML.

    Returns:
        La demande de livraisons.

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
    heure_depart = _heure_en_secondes(
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
