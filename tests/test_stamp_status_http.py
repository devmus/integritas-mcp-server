import respx
import httpx
from fastapi.testclient import TestClient
from integritas_mcp_server.http_app import app

UID_SUCCESS_1 = "0x54C8EF1CFCE47CCB1ACE"
UID_SUCCESS_2 = "0xANOTHER_SUCCESS_UID"
UID_NOT_FOUND = "0xEDA114A9FDE6AC51DC0B"
UID_PENDING_1 = "0xPENDING_UID_1"
UID_PENDING_2 = "0xPENDING_UID_2"

# Helper to create a full API response payload
def create_api_response(data_items: list[dict]) -> dict:
    return {
        "apiVersion": 1, "requestId": "test", "status": "success", "statusCode": 200,
        "message": "UID statuses fetched", "timestamp": "2025-09-02T07:38:17.146Z",
        "data": data_items
    }

# Sample data items for responses
SUCCESS_ITEM_1 = {
    "status": True, "uid": UID_SUCCESS_1,
    "data": "0x941D99478C9F1A73BE508CA1781F654C6B75D1239DC04C71BADCE5DEA7D8C591",
    "number": 201, "datecreated": "2025-09-02 07:37:15",
    "datestamped": "2025-09-02 07:38:03",
    "root": "0xEE0E2FE82376833A8571E057D1F4BE173B0676E2EAA381456C3F8A0D1C36399B",
    "proof": "0x000100000100", "address": "0xFFEEDD", "onchain": True
}

PENDING_ITEM_1 = {
    "status": True, "uid": UID_PENDING_1,
    "data": "0x941D99478C9F1A73BE508CA1781F654C6B75D1239DC04C71BADCE5DEA7D8C591",
    "number": 201, "datecreated": "2025-09-02 07:37:15", "onchain": False
}

PENDING_ITEM_2 = {
    "status": True, "uid": UID_PENDING_2,
    "data": "0x941D99478C9F1A73BE508CA1781F654C6B75D1239DC04C71BADCE5DEA7D8C591",
    "number": 201, "datecreated": "2025-09-02 07:37:15", "onchain": False
}

ERROR_ITEM_NOT_FOUND = {
    "status": False, "uid": UID_NOT_FOUND, "error": "UID not found"
}

@respx.mock
def test_http_stamp_status_success_and_fail():
    """Test a mixed request with one success and one not-found UID."""
    respx.post("https://upstream.example/v1/timestamp/status/").mock(
        return_value=httpx.Response(200, json=create_api_response([SUCCESS_ITEM_1, ERROR_ITEM_NOT_FOUND]))
    )

    client = TestClient(app)
    r = client.post("/v1/timestamp/status", json={"uids": [UID_SUCCESS_1, UID_NOT_FOUND]})

    assert r.status_code == 200
    response_data = r.json()["data"]
    assert len(response_data) == 2

    success_res = next((item for item in response_data if item["uid"] == UID_SUCCESS_1), None)
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

    route = respx.post("https://upstream.example/v1/timestamp/status/").mock(
        return_value=httpx.Response(200, json=create_api_response([SUCCESS_ITEM_1]))
    )

    client = TestClient(app)
    client.post(
        "/v1/timestamp/status",
        json={"uids": [UID_SUCCESS_1]},
        headers={"x-api-key": "from_header"}
    )

    assert route.call_count == 1
    assert route.calls.last.request.headers["x-api-key"] == "from_header"

@respx.mock
def test_http_stamp_status_polling_behavior(monkeypatch):
    """Test that the HTTP endpoint correctly handles polling for pending UIDs."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.MAX_ATTEMPTS", 3)

    # First response: both pending
    # Second response: UID_PENDING_1 succeeds, UID_PENDING_2 still pending
    # Third response: UID_PENDING_2 succeeds
    respx.post("https://upstream.example/v1/timestamp/status/").side_effect = [
        httpx.Response(200, json=create_api_response([PENDING_ITEM_1, PENDING_ITEM_2])),
        httpx.Response(200, json=create_api_response([{**SUCCESS_ITEM_1, "uid": UID_PENDING_1}, PENDING_ITEM_2])),
        httpx.Response(200, json=create_api_response([{**SUCCESS_ITEM_1, "uid": UID_PENDING_1}, {**SUCCESS_ITEM_1, "uid": UID_PENDING_2, "onchain": True}]))
    ]

    client = TestClient(app)
    r = client.post("/v1/timestamp/status", json={"uids": [UID_PENDING_1, UID_PENDING_2]})

    assert r.status_code == 200
    response_data = r.json()["data"]
    assert len(response_data) == 2

    # Verify both UIDs are now successful
    success_1 = next((item for item in response_data if item["uid"] == UID_PENDING_1), None)
    assert success_1 is not None
    assert success_1["onchain"] is True

    success_2 = next((item for item in response_data if item["uid"] == UID_PENDING_2), None)
    assert success_2 is not None
    assert success_2["onchain"] is True

    assert respx.calls.call_count == 3

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
