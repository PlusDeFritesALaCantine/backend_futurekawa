import pytest
import respx
import httpx
from app import config

BRESIL_URL = "http://api_futurekawa:8001"
EQUATEUR_URL = "http://equateur-api:8001"

FAKE_LOTS = [{"id": "L1", "pays": "bresil", "exploitation": "X",
              "entrepot_id": "e1", "date_stockage": "2026-05-19", "statut": "conforme"}]
FAKE_ALERTES = {"lots_problematiques": [{"lot": FAKE_LOTS[0], "raison": "test"}],
                "mesures_hors_seuil": []}
FAKE_LATEST = [{"id": "M1", "entrepot_id": "e1", "temperature": 29.5,
                "humidity": 54.1, "timestamp": "2026-05-29T10:00:00Z"}]


@pytest.fixture(autouse=True)
def patch_pays_urls(monkeypatch):
    urls = {"bresil": BRESIL_URL, "equateur": EQUATEUR_URL}
    monkeypatch.setattr(config, "PAYS_URLS", urls)
    import app.routers.dashboard as dash
    monkeypatch.setattr(dash, "PAYS_URLS", urls)


@respx.mock
def test_dashboard_bresil_ok_equateur_offline(client):
    respx.get(f"{BRESIL_URL}/lots").mock(return_value=httpx.Response(200, json=FAKE_LOTS))
    respx.get(f"{BRESIL_URL}/alertes").mock(return_value=httpx.Response(200, json=FAKE_ALERTES))
    respx.get(f"{BRESIL_URL}/mesures/latest").mock(return_value=httpx.Response(200, json=FAKE_LATEST))
    respx.get(f"{EQUATEUR_URL}/lots").mock(side_effect=httpx.ConnectError("offline"))
    respx.get(f"{EQUATEUR_URL}/alertes").mock(side_effect=httpx.ConnectError("offline"))
    respx.get(f"{EQUATEUR_URL}/mesures/latest").mock(side_effect=httpx.ConnectError("offline"))

    r = client.get("/dashboard")
    assert r.status_code == 200
    data = r.json()
    pays_list = {p["nom"]: p for p in data["pays"]}

    assert pays_list["bresil"]["status"] == "ok"
    assert pays_list["bresil"]["nb_lots"] == 1
    assert pays_list["bresil"]["nb_alertes"] == 1
    assert pays_list["bresil"]["derniere_mesure"]["temperature"] == 29.5

    assert pays_list["equateur"]["status"] == "indisponible"
    assert pays_list["equateur"]["nb_lots"] is None
    assert pays_list["equateur"]["derniere_mesure"] is None


@respx.mock
def test_dashboard_tous_offline(client):
    for url in [BRESIL_URL, EQUATEUR_URL]:
        respx.get(f"{url}/lots").mock(side_effect=httpx.ConnectError("offline"))
        respx.get(f"{url}/alertes").mock(side_effect=httpx.ConnectError("offline"))
        respx.get(f"{url}/mesures/latest").mock(side_effect=httpx.ConnectError("offline"))

    r = client.get("/dashboard")
    assert r.status_code == 200
    for pays in r.json()["pays"]:
        assert pays["status"] == "indisponible"


@respx.mock
def test_dashboard_sans_alertes(client):
    alertes_vides = {"lots_problematiques": [], "mesures_hors_seuil": []}
    respx.get(f"{BRESIL_URL}/lots").mock(return_value=httpx.Response(200, json=FAKE_LOTS))
    respx.get(f"{BRESIL_URL}/alertes").mock(return_value=httpx.Response(200, json=alertes_vides))
    respx.get(f"{BRESIL_URL}/mesures/latest").mock(return_value=httpx.Response(200, json=[]))
    respx.get(f"{EQUATEUR_URL}/lots").mock(side_effect=httpx.ConnectError("offline"))
    respx.get(f"{EQUATEUR_URL}/alertes").mock(side_effect=httpx.ConnectError("offline"))
    respx.get(f"{EQUATEUR_URL}/mesures/latest").mock(side_effect=httpx.ConnectError("offline"))

    r = client.get("/dashboard")
    pays_bresil = next(p for p in r.json()["pays"] if p["nom"] == "bresil")
    assert pays_bresil["nb_alertes"] == 0
    assert pays_bresil["derniere_mesure"] is None
