import pytest
import respx
import httpx
from integritas_mcp_server.models import StampStatusRequest, StampStatusResultSuccess, StampStatusResultError, StampStatusResultPending
from integritas_mcp_server.services.stamp_status import get_definitive_stamp_status, MAX_ATTEMPTS

UID_SUCCESS_1 = "0x54C8EF1CFCE47CCB1ACE"
UID_SUCCESS_2 = "0xANOTHER_SUCCESS_UID"
UID_NOT_FOUND = "0xEDA114A9FDE6AC51DC0B"
UID_PENDING_1 = "0xPENDING_UID_1"
UID_PENDING_2 = "0xPENDING_UID_2"
UID_PROOF_ERROR = "0xPROOF_ERROR_UID"

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

SUCCESS_ITEM_2 = {**SUCCESS_ITEM_1, "uid": UID_SUCCESS_2}

PENDING_ITEM_1 = {
    "status": True, "uid": UID_PENDING_1, 
    "data": "0x941D99478C9F1A73BE508CA1781F654C6B75D1239DC04C71BADCE5DEA7D8C591",
    "number": 201, "datecreated": "2025-09-02 07:37:15", "onchain": False
}

PENDING_ITEM_2 = {**PENDING_ITEM_1, "uid": UID_PENDING_2}

ERROR_ITEM_NOT_FOUND = {
    "status": False, "uid": UID_NOT_FOUND, "error": "UID not found"
}

ERROR_ITEM_GENERIC = {
    "status": False, "uid": UID_PENDING_1, "error": "Generic error from upstream"
}

ERROR_ITEM_PROOF = {
    "status": True, "uid": UID_PROOF_ERROR, "onchain": False, "proof": "ERROR", "error": "Proof generation failed"
}

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_all_success_direct():
    """Test multiple UIDs that are all successfully on-chain in the first response."""
    respx.post("https://upstream.example/v1/timestamp/status/").mock(
        return_value=httpx.Response(200, json=create_api_response([SUCCESS_ITEM_1, SUCCESS_ITEM_2]))
    )
    req = StampStatusRequest(uids=[UID_SUCCESS_1, UID_SUCCESS_2])
    results = await get_definitive_stamp_status(req)

    assert len(results) == 2
    assert all(isinstance(r, StampStatusResultSuccess) for r in results)
    assert {r.uid for r in results} == {UID_SUCCESS_1, UID_SUCCESS_2}
    assert respx.calls.call_count == 1

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_mixed_initial_response():
    """Test a mixed initial response with success, pending, and error."""
    respx.post("https://upstream.example/v1/timestamp/status/").mock(
        return_value=httpx.Response(200, json=create_api_response([SUCCESS_ITEM_1, PENDING_ITEM_1, ERROR_ITEM_NOT_FOUND]))
    )
    req = StampStatusRequest(uids=[UID_SUCCESS_1, UID_PENDING_1, UID_NOT_FOUND])
    results = await get_definitive_stamp_status(req)

    assert len(results) == 3
    uids_to_status = {r.uid: type(r) for r in results}
    assert uids_to_status[UID_SUCCESS_1] == StampStatusResultSuccess
    assert uids_to_status[UID_PENDING_1] == StampStatusResultPending
    assert uids_to_status[UID_NOT_FOUND] == StampStatusResultError
    assert respx.calls.call_count == MAX_ATTEMPTS

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_polling_all_succeed(monkeypatch):
    """Test that polling continues until all UIDs succeed."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    
    # First response: both pending
    # Second response: UID_PENDING_1 succeeds, UID_PENDING_2 still pending
    # Third response: UID_PENDING_2 succeeds
    respx.post("https://upstream.example/v1/timestamp/status/").side_effect = [
        httpx.Response(200, json=create_api_response([PENDING_ITEM_1, PENDING_ITEM_2])),
        httpx.Response(200, json=create_api_response([{**SUCCESS_ITEM_1, "uid": UID_PENDING_1}, PENDING_ITEM_2])),
        httpx.Response(200, json=create_api_response([{**SUCCESS_ITEM_1, "uid": UID_PENDING_1}, {**SUCCESS_ITEM_2, "uid": UID_PENDING_2}])),
    ]

    req = StampStatusRequest(uids=[UID_PENDING_1, UID_PENDING_2])
    results = await get_definitive_stamp_status(req)

    assert len(results) == 2
    assert all(isinstance(r, StampStatusResultSuccess) for r in results)
    assert {r.uid for r in results} == {UID_PENDING_1, UID_PENDING_2}
    assert respx.calls.call_count == 3

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_polling_some_error_some_succeed(monkeypatch):
    """Test that polling handles errors for some UIDs while others succeed."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    
    # First response: PENDING_1 pending, PENDING_2 pending
    # Second response: PENDING_1 errors, PENDING_2 succeeds
    respx.post("https://upstream.example/v1/timestamp/status/").side_effect = [
        httpx.Response(200, json=create_api_response([PENDING_ITEM_1, PENDING_ITEM_2])),
        httpx.Response(200, json=create_api_response([ERROR_ITEM_GENERIC, {**SUCCESS_ITEM_2, "uid": UID_PENDING_2}])),
    ]

    req = StampStatusRequest(uids=[UID_PENDING_1, UID_PENDING_2])
    results = await get_definitive_stamp_status(req)

    assert len(results) == 2
    uids_to_status = {r.uid: type(r) for r in results}
    assert uids_to_status[UID_PENDING_1] == StampStatusResultError
    assert uids_to_status[UID_PENDING_2] == StampStatusResultSuccess
    assert respx.calls.call_count == 2

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_polling_timeout_returns_pending(monkeypatch):
    """Test that polling times out and returns pending status for unresolved UIDs."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.MAX_ATTEMPTS", 3)

    # Always return pending for both UIDs
    respx.post("https://upstream.example/v1/timestamp/status/").mock(
        return_value=httpx.Response(200, json=create_api_response([PENDING_ITEM_1, PENDING_ITEM_2]))
    )

    req = StampStatusRequest(uids=[UID_PENDING_1, UID_PENDING_2])
    results = await get_definitive_stamp_status(req)

    assert len(results) == 2
    assert all(isinstance(r, StampStatusResultPending) for r in results)
    assert {r.uid for r in results} == {UID_PENDING_1, UID_PENDING_2}
    assert respx.calls.call_count == 3

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_batch_request_error(monkeypatch):
    """Test that a batch request error marks all pending UIDs as errors."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    
    # First response: both pending
    # Second response: 500 error for the batch request
    respx.post("https://upstream.example/v1/timestamp/status/").side_effect = [
        httpx.Response(200, json=create_api_response([PENDING_ITEM_1, PENDING_ITEM_2])),
        httpx.Response(500, text="Upstream internal error"),
    ]

    req = StampStatusRequest(uids=[UID_PENDING_1, UID_PENDING_2])
    results = await get_definitive_stamp_status(req)

    assert len(results) == 2
    assert all(isinstance(r, StampStatusResultError) for r in results)
    assert {r.uid for r in results} == {UID_PENDING_1, UID_PENDING_2}
    assert "Upstream internal error" in results[0].error
    assert respx.calls.call_count == 2

@pytest.mark.asyncio
@respx.mock
async def test_stamp_status_proof_error_is_error(monkeypatch):
    """Test that a UID with status=True, onchain=False, and proof='ERROR' is marked as an error."""
    monkeypatch.setattr("integritas_mcp_server.services.stamp_status.POLLING_INTERVAL_SECONDS", 0.01)
    
    respx.post("https://upstream.example/v1/timestamp/status/").mock(
        return_value=httpx.Response(200, json=create_api_response([ERROR_ITEM_PROOF]))
    )

    req = StampStatusRequest(uids=[UID_PROOF_ERROR])
    results = await get_definitive_stamp_status(req)

    assert len(results) == 1
    assert isinstance(results[0], StampStatusResultError)
    assert results[0].uid == UID_PROOF_ERROR
    assert "Proof generation failed" in results[0].error
    assert respx.calls.call_count == 1
