import pytest
from fastapi.testclient import TestClient

from backend_futurekawa.odoo.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
