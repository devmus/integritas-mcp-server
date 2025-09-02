# tests/test_stamp_status_unit.py
import pytest
import respx
import httpx
from integritas_mcp_server.models import StampStatusRequest
from integritas_mcp_server.services.stamp_status import perform_stamp_status, PATH_STAMP_STATUS

UID_SUCCESS = "0x54C8EF1CFCE47CCB1ACE"
UID_NOT_FOUND = "0xEDA114A9FDE6AC51DC0B"
UID_PENDING = "0xPENDING"

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

PENDING_PAYLOAD = {
    "apiVersion": 1, "requestId": "test", "status": "success", "statusCode": 200,
    "message": "UID statuses fetched", "timestamp": "2025-09-02T07:37:23.408Z",
    "data": [{
        "status": True, "uid": UID_PENDING, 
        "data": "0x941D99478C9F1A73BE508CA1781F654C6B75D1239DC04C71BADCE5DEA7D8C591",
        "number": 201, "datecreated": "2025-09-02 07:37:15", "onchain": False
    }]
}

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_success_direct():
    """Test a UID that is already successfully on-chain."""
    respx.get(f"https://upstream.example{PATH_STAMP_STATUS.format(uid=UID_SUCCESS)}").mock(
        return_value=httpx.Response(200, json=SUCCESS_PAYLOAD)
    )
    req = StampStatusRequest(uids=[UID_SUCCESS])
    results = await perform_stamp_status(req)
    assert len(results) == 1
    res = results[0]
    assert res.uid == UID_SUCCESS
    assert res.onchain is True
    assert res.root is not None

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_not_found():
    """Test a UID that is not found (404)."""
    respx.get(f"https://upstream.example{PATH_STAMP_STATUS.format(uid=UID_NOT_FOUND)}").mock(
        return_value=httpx.Response(404)
    )
    req = StampStatusRequest(uids=[UID_NOT_FOUND])
    results = await perform_stamp_status(req)
    assert len(results) == 1
    res = results[0]
    assert res.uid == UID_NOT_FOUND
    assert res.status is False
    assert "not found" in res.error.lower()

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_polling_success(monkeypatch):
    """Test a UID that is pending then succeeds."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    
    # Mock the first call as pending, the second as success
    status_route = respx.get(f"https://upstream.example{PATH_STAMP_STATUS.format(uid=UID_PENDING)}")
    status_route.side_effect = [
        httpx.Response(200, json=PENDING_PAYLOAD),
        httpx.Response(200, json={**SUCCESS_PAYLOAD, "data": [{**SUCCESS_PAYLOAD["data"][0], "uid": UID_PENDING}]}),
    ]

    req = StampStatusRequest(uids=[UID_PENDING])
    results = await perform_stamp_status(req)
    
    assert len(results) == 1
    res = results[0]
    assert res.uid == UID_PENDING
    assert res.onchain is True
    assert res.root is not None
    assert status_route.call_count == 2

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_polling_timeout(monkeypatch):
    """Test that polling times out if status never becomes final."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.MAX_ATTEMPTS", 3)

    respx.get(f"https://upstream.example{PATH_STAMP_STATUS.format(uid=UID_PENDING)}").mock(
        return_value=httpx.Response(200, json=PENDING_PAYLOAD)
    )

    req = StampStatusRequest(uids=[UID_PENDING])
    results = await perform_stamp_status(req)

    assert len(results) == 1
    res = results[0]
    assert res.status is False
    assert "timed out" in res.error.lower()
