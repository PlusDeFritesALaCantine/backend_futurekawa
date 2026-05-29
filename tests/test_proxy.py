import pytest
import respx
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app import config

BRESIL_URL = "http://api_futurekawa:8001"

FAKE_LOTS = [
    {"id": "LOT-BR-001", "pays": "bresil", "exploitation": "Fazenda A",
     "entrepot_id": "e1", "date_stockage": "2026-05-19", "statut": "conforme"},
]
FAKE_ALERTES = {"lots_problematiques": [], "mesures_hors_seuil": []}


@pytest.fixture(autouse=True)
def patch_pays_urls(monkeypatch):
    monkeypatch.setattr(config, "PAYS_URLS", {"bresil": BRESIL_URL})
    import app.routers.pays as pays_router
    monkeypatch.setattr(pays_router, "PAYS_URLS", {"bresil": BRESIL_URL})
    import app.routers.dashboard as dash_router
    monkeypatch.setattr(dash_router, "PAYS_URLS", {"bresil": BRESIL_URL})


@respx.mock
def test_proxy_lots_ok(client):
    respx.get(f"{BRESIL_URL}/lots").mock(return_value=httpx.Response(200, json=FAKE_LOTS))
    r = client.get("/pays/bresil/lots")
    assert r.status_code == 200
    assert r.json()[0]["id"] == "LOT-BR-001"


@respx.mock
def test_proxy_lots_offline(client):
    respx.get(f"{BRESIL_URL}/lots").mock(side_effect=httpx.ConnectError("offline"))
    r = client.get("/pays/bresil/lots")
    assert r.status_code == 503


@respx.mock
def test_proxy_alertes_ok(client):
    respx.get(f"{BRESIL_URL}/alertes").mock(
        return_value=httpx.Response(200, json=FAKE_ALERTES)
    )
    r = client.get("/pays/bresil/alertes")
    assert r.status_code == 200
    assert "lots_problematiques" in r.json()


@respx.mock
def test_proxy_alertes_offline(client):
    respx.get(f"{BRESIL_URL}/alertes").mock(side_effect=httpx.ConnectError("offline"))
    r = client.get("/pays/bresil/alertes")
    assert r.status_code == 503


def test_proxy_pays_inconnu(client):
    r = client.get("/pays/allemagne/lots")
    assert r.status_code == 404


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
