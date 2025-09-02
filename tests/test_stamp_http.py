# tests/test_stamp_http.py
import respx
import httpx
from fastapi.testclient import TestClient
from integritas_mcp_server.http_app import app

def test_http_stamp():
    with respx.mock:
        respx.post("https://upstream.example/v1/timestamp/post").mock(
            return_value=httpx.Response(200, json={"uid":"u1"})
        )
        client = TestClient(app)
        r = client.post("/v1/timestamp/post", json={"hash":"aabb"})
        assert r.status_code == 200
        assert r.json()["uid"] == "u1"