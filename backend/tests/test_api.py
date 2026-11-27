"""Tests de l'API : upload de la carte et des livraisons, calcul de la tournée."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api

RESSOURCES = Path(__file__).resolve().parent.parent.parent / "ressources"
PETIT_PLAN = RESSOURCES / "petitPlan.xml"
DEMANDE_PETIT1 = RESSOURCES / "demandePetit1.xml"  # sur petitPlan
DEMANDE_GRAND9 = RESSOURCES / "demandeGrand9.xml"  # sur grandPlan


@pytest.fixture
def client():
    """Un client sur une API vide (aucune carte, aucune livraison)."""
    api.planification = None
    api.current_coursier_id = 1
    yield TestClient(api.app)
    api.planification = None
    api.current_coursier_id = 1


def upload(client, url, chemin: Path):
    with chemin.open("rb") as f:
        return client.post(url, files={"file": (chemin.name, f, "text/xml")})


def upload_texte(client, url, contenu: str):
    return client.post(url, files={"file": ("fichier.xml", contenu.encode(), "text/xml")})


def erreur(reponse, status: int, code: str) -> dict:
    """Vérifie qu'une réponse est une erreur au format commun et la renvoie."""
    assert reponse.status_code == status, reponse.text
    corps = reponse.json()["erreur"]
    assert corps["code"] == code
    assert isinstance(corps["message"], str) and corps["message"]
    assert isinstance(corps["details"], dict)
    return corps


@pytest.fixture
def client_avec_carte(client):
    assert upload(client, "/api/upload-carte", PETIT_PLAN).status_code == 200
    return client


@pytest.fixture
def client_avec_livraisons(client_avec_carte):
    reponse = upload(client_avec_carte, "/api/upload-livraisons", DEMANDE_PETIT1)
    assert reponse.status_code == 200
    return client_avec_carte


class TestSansDonnees:
    def test_tournee_sans_carte(self, client):
        erreur(client.get("/api/tournee"), 409, "CARTE_NON_CHARGEE")

    def test_route_graph_sans_carte(self, client):
        erreur(client.get("/api/route-graph"), 409, "CARTE_NON_CHARGEE")

    def test_livraisons_sans_carte(self, client):
        reponse = upload(client, "/api/upload-livraisons", DEMANDE_PETIT1)
        erreur(reponse, 409, "CARTE_NON_CHARGEE")


class TestUploadCarte:
    def test_carte_valide(self, client):
        reponse = upload(client, "/api/upload-carte", PETIT_PLAN)
        assert reponse.status_code == 200
        assert reponse.json()["intersections"] > 0
        assert reponse.json()["troncons"] > 0
        assert client.get("/api/route-graph").status_code == 200

    def test_xml_mal_forme(self, client):
        reponse = upload_texte(client, "/api/upload-carte", "pas du xml")
        assert "XML mal formé" in erreur(reponse, 400, "CARTE_INVALIDE")["message"]
        assert api.planification is None

    def test_fichier_de_livraisons_a_la_place_de_la_carte(self, client):
        reponse = upload(client, "/api/upload-carte", DEMANDE_PETIT1)
        erreur(reponse, 400, "CARTE_INVALIDE")
        assert api.planification is None

    def test_carte_invalide_garde_l_ancienne(self, client_avec_livraisons):
        reponse = upload_texte(client_avec_livraisons, "/api/upload-carte", "pas du xml")
        erreur(reponse, 400, "CARTE_INVALIDE")
        assert client_avec_livraisons.get("/api/tournee").status_code == 200

    def test_nouvelle_carte_oublie_les_livraisons(self, client_avec_livraisons):
        upload(client_avec_livraisons, "/api/upload-carte", PETIT_PLAN)
        erreur(client_avec_livraisons.get("/api/tournee"), 409, "LIVRAISONS_NON_CHARGEES")

    def test_n_ecrit_rien_dans_ressources(self, client):
        avant = sorted(p.name for p in RESSOURCES.iterdir())
        with PETIT_PLAN.open("rb") as f:
            client.post("/api/upload-carte", files={"file": ("../nouveau.xml", f, "text/xml")})
        assert sorted(p.name for p in RESSOURCES.iterdir()) == avant
        assert not (RESSOURCES.parent / "nouveau.xml").exists()


class TestUploadLivraisons:
    def test_livraisons_valides(self, client_avec_carte):
        reponse = upload(client_avec_carte, "/api/upload-livraisons", DEMANDE_PETIT1)
        assert reponse.status_code == 200
        data = reponse.json()
        assert data["heure_depart"] == 8 * 3600
        assert len(data["livraisons"]) == 1

    def test_xml_mal_forme(self, client_avec_carte):
        reponse = upload_texte(client_avec_carte, "/api/upload-livraisons", "pas du xml")
        erreur(reponse, 400, "LIVRAISONS_INVALIDES")

    def test_adresses_absentes_de_la_carte(self, client_avec_carte):
        reponse = upload(client_avec_carte, "/api/upload-livraisons", DEMANDE_GRAND9)
        corps = erreur(reponse, 400, "ADRESSES_INCONNUES")
        assert "absentes de la carte" in corps["message"]
        assert corps["details"]["adresses"]

    def test_fichier_invalide_oublie_les_anciennes_livraisons(self, client_avec_livraisons):
        upload_texte(client_avec_livraisons, "/api/upload-livraisons", "pas du xml")
        erreur(client_avec_livraisons.get("/api/tournee"), 409, "LIVRAISONS_NON_CHARGEES")


class TestTournee:
    def test_tournee_sans_livraisons(self, client_avec_carte):
        erreur(client_avec_carte.get("/api/tournee"), 409, "LIVRAISONS_NON_CHARGEES")

    def test_tournee_calculee_apres_assignation(self, client_avec_livraisons):
        client = client_avec_livraisons
        client.post("/api/add-coursiers", json=[{"prenom": "Marie", "nom": "Dupont"}])
        assert client.post("/api/coursiers/1/assignLivraisons", json=[1]).status_code == 200

        reponse = client.get("/api/tournee")
        assert reponse.status_code == 200
        coursiers = reponse.json()
        assert [c["id"] for c in coursiers] == [1]
        chemin = coursiers[0]["tournee"]["chemin"]
        entrepot = 342873658  # adresse de l'entrepôt dans demandePetit1.xml
        assert chemin[0]["adresse"] == entrepot
        assert chemin[-1]["adresse"] == entrepot
        types = [p["type"] for p in chemin]
        assert types.index("enlevement") < types.index("livraison")


class TestFormatDesErreurs:
    def test_tournee_impossible(self, client_avec_livraisons, monkeypatch):
        from erreurs import TourneeImpossible

        def impossible(self):
            raise TourneeImpossible("arrêts inaccessibles")
        monkeypatch.setattr(api.Planification, "calculer_tournee", impossible)
        erreur(client_avec_livraisons.get("/api/tournee"), 422, "TOURNEE_IMPOSSIBLE")

    def test_bug_donne_une_500_lisible_avec_cors(self, client_avec_livraisons, monkeypatch):
        def bug(self):
            raise TypeError("bug de programmation")
        monkeypatch.setattr(api.Planification, "calculer_tournee", bug)
        reponse = client_avec_livraisons.get(
            "/api/tournee", headers={"Origin": "http://localhost:5173"}
        )
        corps = erreur(reponse, 500, "ERREUR_INTERNE")
        assert "bug de programmation" not in corps["message"]  # pas de fuite interne
        # sans cet en-tête, le navigateur cacherait la réponse au frontend
        assert reponse.headers["access-control-allow-origin"] == "http://localhost:5173"

    def test_champ_file_absent(self, client):
        corps = erreur(client.post("/api/upload-carte"), 422, "REQUETE_INVALIDE")
        assert corps["details"]["erreurs"]

    def test_route_inconnue(self, client):
        erreur(client.get("/api/nexiste-pas"), 404, "HTTP_404")
