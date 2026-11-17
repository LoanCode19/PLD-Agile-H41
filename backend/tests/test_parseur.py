"""Tests du parseur du fichier XML des livraisons."""

from pathlib import Path

import pytest

from backend.livraisons.parseur_livraisons import FichierLivraisonsInvalide, charger_livraisons

CHEMIN_EXEMPLE = Path(__file__).parent / "data" / "livraisons_exemple.xml"


def ecrire_xml(tmp_path: Path, contenu: str) -> Path:
    chemin = tmp_path / "livraisons.xml"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


class TestChargementValide:
    def test_lit_l_entrepot(self):
        demande = charger_livraisons(CHEMIN_EXEMPLE)
        assert demande.adresse_entrepot == 25327124
        assert demande.heure_depart == 8 * 3600  # 08:00 en secondes

    def test_lit_les_livraisons_dans_l_ordre(self):
        demande = charger_livraisons(CHEMIN_EXEMPLE)
        assert [l.adresse_enlevement for l in demande.livraisons] == [
            26464256,
            984553611,
            1678996781,
        ]
        premiere = demande.livraisons[0]
        assert premiere.adresse_livraison == 239603465
        assert premiere.duree_enlevement == 0
        assert premiere.duree_livraison == 600

    def test_sans_livraison_est_valide(self, tmp_path):
        chemin = ecrire_xml(
            tmp_path,
            '<demandeDeLivraisons>'
            '<entrepot adresse="1" heureDepart="08:00"/>'
            '</demandeDeLivraisons>',
        )
        demande = charger_livraisons(chemin)
        assert demande.livraisons == ()


class TestErreursDeFichier:
    def test_fichier_introuvable(self, tmp_path):
        with pytest.raises(FichierLivraisonsInvalide, match="Lecture impossible"):
            charger_livraisons(tmp_path / "inexistant.xml")

    def test_xml_mal_forme(self, tmp_path):
        chemin = ecrire_xml(tmp_path, "<demandeDeLivraisons><entrepot>")
        with pytest.raises(FichierLivraisonsInvalide, match="XML mal forme"):
            charger_livraisons(chemin)


class TestErreursDeFormat:
    def test_racine_inattendue(self, tmp_path):
        chemin = ecrire_xml(
            tmp_path,
            '<carte><entrepot adresse="1" heureDepart="08:00"/></carte>',
        )
        with pytest.raises(FichierLivraisonsInvalide, match="Racine attendue"):
            charger_livraisons(chemin)

    def test_entrepot_manquant(self, tmp_path):
        chemin = ecrire_xml(tmp_path, "<demandeDeLivraisons/>")
        with pytest.raises(FichierLivraisonsInvalide, match="entrepot.*manquant"):
            charger_livraisons(chemin)

    def test_attribut_manquant_sur_l_entrepot(self, tmp_path):
        chemin = ecrire_xml(
            tmp_path,
            '<demandeDeLivraisons><entrepot adresse="1"/></demandeDeLivraisons>',
        )
        with pytest.raises(FichierLivraisonsInvalide, match="heureDepart.*manquant"):
            charger_livraisons(chemin)

    @pytest.mark.parametrize("heure", ["8h00", "24:00", "08:60", "08", ""])
    def test_heure_depart_invalide(self, tmp_path, heure):
        chemin = ecrire_xml(
            tmp_path,
            f'<demandeDeLivraisons>'
            f'<entrepot adresse="1" heureDepart="{heure}"/>'
            f'</demandeDeLivraisons>',
        )
        with pytest.raises(FichierLivraisonsInvalide, match="heureDepart"):
            charger_livraisons(chemin)

    def test_adresse_non_entiere(self, tmp_path):
        chemin = ecrire_xml(
            tmp_path,
            '<demandeDeLivraisons>'
            '<entrepot adresse="abc" heureDepart="08:00"/>'
            '</demandeDeLivraisons>',
        )
        with pytest.raises(FichierLivraisonsInvalide, match="doit etre un entier"):
            charger_livraisons(chemin)

    @pytest.mark.parametrize(
        "attribut", ["adresseEnlevement", "adresseLivraison",
                     "dureeEnlevement", "dureeLivraison"]
    )
    def test_attribut_manquant_sur_une_livraison(self, tmp_path, attribut):
        attrs = {
            "adresseEnlevement": "1",
            "adresseLivraison": "2",
            "dureeEnlevement": "60",
            "dureeLivraison": "60",
        }
        del attrs[attribut]
        attrs_xml = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        chemin = ecrire_xml(
            tmp_path,
            f'<demandeDeLivraisons>'
            f'<entrepot adresse="1" heureDepart="08:00"/>'
            f'<livraison {attrs_xml}/>'
            f'</demandeDeLivraisons>',
        )
        with pytest.raises(FichierLivraisonsInvalide, match=f"{attribut}.*manquant"):
            charger_livraisons(chemin)

    def test_duree_negative(self, tmp_path):
        chemin = ecrire_xml(
            tmp_path,
            '<demandeDeLivraisons>'
            '<entrepot adresse="1" heureDepart="08:00"/>'
            '<livraison adresseEnlevement="1" adresseLivraison="2"'
            ' dureeEnlevement="-5" dureeLivraison="60"/>'
            '</demandeDeLivraisons>',
        )
        with pytest.raises(FichierLivraisonsInvalide, match="doit etre positif"):
            charger_livraisons(chemin)

    def test_message_d_erreur_indique_la_livraison_concernee(self, tmp_path):
        chemin = ecrire_xml(
            tmp_path,
            '<demandeDeLivraisons>'
            '<entrepot adresse="1" heureDepart="08:00"/>'
            '<livraison adresseEnlevement="1" adresseLivraison="2"'
            ' dureeEnlevement="60" dureeLivraison="60"/>'
            '<livraison adresseEnlevement="1" adresseLivraison="2"'
            ' dureeEnlevement="soixante" dureeLivraison="60"/>'
            '</demandeDeLivraisons>',
        )
        with pytest.raises(FichierLivraisonsInvalide, match="Livraison 2"):
            charger_livraisons(chemin)
