# tests/test_server.py
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock

from integritas_mcp_server.stdio_app import stamp_status
from integritas_mcp_server.models import StampStatusRequest, StampStatusResultError, StampStatusResultSuccess, StampStatusResponse

@pytest.mark.asyncio
async def test_stdio_stamp_status(monkeypatch):
    """Test that the stdio stamp_status tool correctly calls the service and wraps the response."""
    # 1. Arrange
    # Mock the underlying service function
    mock_results = [
        StampStatusResultSuccess(
            status=True, uid="0x123", data="mock_data", number=1, datecreated="now",
            datestamped="later", root="mock_root", proof="mock_proof", address="mock_address", onchain=True
        ),
        StampStatusResultError(uid="0x456", error="Mock error")
    ]
    mock_perform_status = AsyncMock(return_value=mock_results)
    monkeypatch.setattr(
        "integritas_mcp_server.stdio_app.get_definitive_stamp_status", # Patch the service function, not the one imported in stdio_app
        mock_perform_status
    )

    # Create a request object
    req = StampStatusRequest(uids=["0x123", "0x456"], api_key="test-key")

    # 2. Act
    # Call the tool function directly
    response = await stamp_status(req, ctx=AsyncMock(request_id="test-req-id")) # Pass a mock context

    # 3. Assert
    # Check that the service was called correctly
    mock_perform_status.assert_called_once_with(req, "test-req-id", api_key="test-key")

    # Check that the response is structured correctly
    assert isinstance(response, StampStatusResponse)
    assert response.requestId == "test-req-id"
    assert len(response.data) == 2
    assert response.data[0].uid == "0x123"
    assert response.data[0].onchain is True
    assert response.data[1].uid == "0x456"
    assert response.data[1].status is False
    assert response.data[1].error == "Mock error"
