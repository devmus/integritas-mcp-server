# tests/test_health_endpoints.py
from fastapi.testclient import TestClient
from integritas_mcp_server.http_app import app

def test_healthz():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
