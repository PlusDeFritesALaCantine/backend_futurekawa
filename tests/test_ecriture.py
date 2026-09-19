"""Écritures relayées par le siège vers les API pays.

Avant, le front envoyait POST /lots au siège, qui n'avait aucune route en
écriture et répondait 404. Ces tests verrouillent le relais et, surtout, la
traduction des statuts : une erreur métier de l'API pays ne doit pas être
maquillée en « pays indisponible ».
"""

import httpx
import pytest
import respx

from app import config

BRESIL_URL = "http://api_futurekawa:8001"

LOT = {
    "id": "LOT-BR-009", "exploitation": "Fazenda Nova",
    "entrepot_id": "entrepot-bresil-1", "date_stockage": "2026-09-01",
}


@pytest.fixture(autouse=True)
def patch_pays_urls(monkeypatch):
    monkeypatch.setattr(config, "PAYS_URLS", {"bresil": BRESIL_URL})
    import app.routers.pays as pays_router
    monkeypatch.setattr(pays_router, "PAYS_URLS", {"bresil": BRESIL_URL})
    import app.routers.dashboard as dash_router
    monkeypatch.setattr(dash_router, "PAYS_URLS", {"bresil": BRESIL_URL})


class TestCreationLot:
    @respx.mock
    def test_creation_relayee(self, client):
        route = respx.post(f"{BRESIL_URL}/lots").mock(
            return_value=httpx.Response(201, json={**LOT, "pays": "bresil", "statut": "conforme"})
        )
        r = client.post("/pays/bresil/lots", json=LOT)

        assert r.status_code == 201
        assert r.json()["id"] == "LOT-BR-009"
        assert route.called

    @respx.mock
    def test_le_pays_de_l_url_fait_foi(self, client):
        route = respx.post(f"{BRESIL_URL}/lots").mock(
            return_value=httpx.Response(201, json={**LOT, "pays": "bresil", "statut": "conforme"})
        )
        client.post("/pays/bresil/lots", json={**LOT, "pays": "colombie"})

        import json as _json
        envoye = _json.loads(route.calls[0].request.content)
        assert envoye["pays"] == "bresil"

    @respx.mock
    def test_conflit_metier_reste_un_409(self, client):
        respx.post(f"{BRESIL_URL}/lots").mock(
            return_value=httpx.Response(409, json={"detail": "Lot déjà existant"})
        )
        r = client.post("/pays/bresil/lots", json=LOT)

        # Le piège serait de tout attraper et de répondre 503 : l'utilisateur
        # croirait le service en panne au lieu de corriger son identifiant.
        assert r.status_code == 409
        assert r.json()["detail"] == "Lot déjà existant"

    @respx.mock
    def test_api_pays_injoignable(self, client):
        respx.post(f"{BRESIL_URL}/lots").mock(side_effect=httpx.ConnectError("offline"))
        r = client.post("/pays/bresil/lots", json=LOT)
        assert r.status_code == 503

    def test_pays_inconnu(self, client):
        assert client.post("/pays/allemagne/lots", json=LOT).status_code == 404


class TestModificationEtSuppression:
    @respx.mock
    def test_patch_relaye(self, client):
        respx.patch(f"{BRESIL_URL}/lots/LOT-BR-009").mock(
            return_value=httpx.Response(200, json={**LOT, "pays": "bresil",
                                                   "exploitation": "Fazenda Modifiee",
                                                   "statut": "conforme"})
        )
        r = client.patch("/pays/bresil/lots/LOT-BR-009", json={"exploitation": "Fazenda Modifiee"})

        assert r.status_code == 200
        assert r.json()["exploitation"] == "Fazenda Modifiee"

    @respx.mock
    def test_delete_relaye_le_204(self, client):
        respx.delete(f"{BRESIL_URL}/lots/LOT-BR-009").mock(
            return_value=httpx.Response(204)
        )
        r = client.delete("/pays/bresil/lots/LOT-BR-009")
        assert r.status_code == 204

    @respx.mock
    def test_suppression_lot_inconnu_reste_un_404(self, client):
        respx.delete(f"{BRESIL_URL}/lots/FANTOME").mock(
            return_value=httpx.Response(404, json={"detail": "Lot introuvable"})
        )
        r = client.delete("/pays/bresil/lots/FANTOME")
        assert r.status_code == 404


class TestMesuresPaginees:
    @respx.mock
    def test_les_parametres_de_pagination_sont_relayes(self, client):
        route = respx.get(f"{BRESIL_URL}/mesures").mock(
            return_value=httpx.Response(200, json={"items": [], "total": 0,
                                                   "limit": 50, "offset": 100})
        )
        r = client.get("/pays/bresil/mesures?limit=50&offset=100&entrepot_id=e1")

        assert r.status_code == 200
        params = dict(route.calls[0].request.url.params)
        assert params["limit"] == "50"
        assert params["offset"] == "100"
        assert params["entrepot_id"] == "e1"

    @respx.mock
    def test_les_filtres_vides_ne_sont_pas_transmis(self, client):
        route = respx.get(f"{BRESIL_URL}/mesures").mock(
            return_value=httpx.Response(200, json={"items": [], "total": 0,
                                                   "limit": 100, "offset": 0})
        )
        client.get("/pays/bresil/mesures")

        params = dict(route.calls[0].request.url.params)
        assert "entrepot_id" not in params
        assert "debut" not in params

    def test_limite_plafonnee(self, client):
        assert client.get("/pays/bresil/mesures?limit=99999").status_code == 422


class TestParametres:
    @respx.mock
    def test_lecture_relayee(self, client):
        respx.get(f"{BRESIL_URL}/parametres/pays/bresil").mock(
            return_value=httpx.Response(200, json={"slug": "bresil", "peremption_jours": 365})
        )
        r = client.get("/pays/bresil/parametres")
        assert r.status_code == 200
        assert r.json()["peremption_jours"] == 365

    @respx.mock
    def test_modification_relayee(self, client):
        route = respx.patch(f"{BRESIL_URL}/parametres/pays/bresil").mock(
            return_value=httpx.Response(200, json={"slug": "bresil", "peremption_jours": 180})
        )
        r = client.patch("/pays/bresil/parametres", json={"peremption_jours": 180})

        assert r.status_code == 200
        assert route.called


class TestJournalAlertes:
    @respx.mock
    def test_journal_relaye(self, client):
        respx.get(f"{BRESIL_URL}/alertes/journal").mock(
            return_value=httpx.Response(200, json={"items": [], "total": 0,
                                                   "limit": 100, "offset": 0})
        )
        r = client.get("/pays/bresil/alertes/journal?statut=ouverte")
        assert r.status_code == 200

    @respx.mock
    def test_acquittement_relaye(self, client):
        respx.patch(f"{BRESIL_URL}/alertes/A1/acquitter").mock(
            return_value=httpx.Response(200, json={"id": "A1", "acquittee_par": "noa"})
        )
        r = client.patch("/pays/bresil/alertes/A1/acquitter", json={"par": "noa"})

        assert r.status_code == 200
        assert r.json()["acquittee_par"] == "noa"


class TestDernieresMesures:
    @respx.mock
    def test_latest_relaye(self, client):
        respx.get(f"{BRESIL_URL}/mesures/latest").mock(
            return_value=httpx.Response(200, json=[
                {"id": "M1", "entrepot_id": "e1", "temperature": 29.0,
                 "humidity": 55.0, "timestamp": "2026-09-19T08:00:00Z"},
            ])
        )
        r = client.get("/pays/bresil/mesures/latest")

        assert r.status_code == 200
        assert len(r.json()) == 1

    @respx.mock
    def test_latest_api_injoignable(self, client):
        respx.get(f"{BRESIL_URL}/mesures/latest").mock(side_effect=httpx.ConnectError("offline"))
        assert client.get("/pays/bresil/mesures/latest").status_code == 503
