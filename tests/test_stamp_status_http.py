# tests/test_stamp_status_http.py
import respx
import httpx
from fastapi.testclient import TestClient
from integritas_mcp_server.http_app import app
from integritas_mcp_server.services.stamp_status import PATH_STAMP_STATUS

UID_SUCCESS = "0x54C8EF1CFCE47CCB1ACE"
UID_NOT_FOUND = "0xEDA114A9FDE6AC51DC0B"

SUCCESS_PAYLOAD = {
    "apiVersion": 1, "requestId": "test", "status": "success", "statusCode": 200,
    "message": "UID statuses fetched", "timestamp": "2025-09-02T07:38:17.146Z",
    "data": [{
        "status": True, "uid": UID_SUCCESS,
        "data": "0x941D99478C9F1A73BE508CA1781F654C6B75D1239DC04C71BADCE5DEA7D8C591",
        "number": 201, "datecreated": "2025-09-02 07:37:15",
        "datestamped": "2025-09-02 07:38:03",
        "root": "0xEE0E2FE82376833A8571E057D1F4BE173B0676E2EAA381456C3F8A0D1C36399B",
        "proof": "0x000100000100", "address": "0xFFEEDD", "onchain": True
    }]
}

@respx.mock
def test_http_stamp_status_success_and_fail():
    """Test a mixed request with one success and one not-found UID."""
    respx.get(f"https://upstream.example{PATH_STAMP_STATUS.format(uid=UID_SUCCESS)}").mock(
        return_value=httpx.Response(200, json=SUCCESS_PAYLOAD)
    )
    respx.get(f"https://upstream.example{PATH_STAMP_STATUS.format(uid=UID_NOT_FOUND)}").mock(
        return_value=httpx.Response(404)
    )

    client = TestClient(app)
    r = client.post("/v1/timestamp/status", json={"uids": [UID_SUCCESS, UID_NOT_FOUND]})
    
    assert r.status_code == 200
    response_data = r.json()["data"]
    assert len(response_data) == 2

    success_res = next((item for item in response_data if item["uid"] == UID_SUCCESS), None)
    assert success_res is not None
    assert success_res["onchain"] is True

    error_res = next((item for item in response_data if item["uid"] == UID_NOT_FOUND), None)
    assert error_res is not None
    assert error_res["status"] is False
    assert "not found" in error_res["error"].lower()

@respx.mock
def test_http_stamp_status_with_api_key(monkeypatch):
    """Test that the API key from the header is correctly forwarded."""
    monkeypatch.setenv("MINIMA_API_KEY", "from_env")
    
    route = respx.get(f"https://upstream.example{PATH_STAMP_STATUS.format(uid=UID_SUCCESS)}").mock(
        return_value=httpx.Response(200, json=SUCCESS_PAYLOAD)
    )

    client = TestClient(app)
    client.post(
        "/v1/timestamp/status", 
        json={"uids": [UID_SUCCESS]},
        headers={"x-api-key": "from_header"}
    )

    assert route.call_count == 1
    assert route.calls.last.request.headers["x-api-key"] == "from_header"


def test_http_stamp_status_no_uids():
    """Test request with empty UID list."""
    client = TestClient(app)
    r = client.post("/v1/timestamp/status", json={"uids": []})
    assert r.status_code == 200 # The request is valid, data is just empty
    assert r.json()["data"] == []


def test_http_stamp_status_bad_request():
    """Test request with invalid body."""
    client = TestClient(app)
    r = client.post("/v1/timestamp/status", json={"wrong_key": []})
    assert r.status_code == 422 # Pydantic validation error
