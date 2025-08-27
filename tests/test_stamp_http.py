# tests/test_stamp_http.py
import respx
import httpx
from fastapi.testclient import TestClient
from integritas_mcp_server.http_app import app
from integritas_mcp_server.config import get_settings

def test_http_stamp():

    with respx.mock:
        respx.post("https://upstream.example/v1/timestamp/post").mock(
            return_value=httpx.Response(200, json={"uid":"u1","tx_id":"t2"})
        )
        client = TestClient(app)
        r = client.post("/tools/stamp", json={"hash":"aabb"})
        assert r.status_code == 200
        assert r.json()["uid"] == "u1"
