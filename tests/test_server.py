# tests/test_server.py
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock

from integritas_mcp_server.stdio_app import stamp_status
from integritas_mcp_server.models import StampStatusRequest, StampStatusResultError

@pytest.mark.asyncio
async def test_stdio_stamp_status(monkeypatch):
    """Test that the stdio stamp_status tool correctly calls the service and wraps the response."""
    # 1. Arrange
    # Mock the underlying service function
    mock_results = [StampStatusResultError(uid="0x123", error="Test error")]
    mock_perform_status = AsyncMock(return_value=mock_results)
    monkeypatch.setattr(
        "integritas_mcp_server.stdio_app.perform_stamp_status",
        mock_perform_status
    )

    # Create a request object
    req = StampStatusRequest(uids=["0x123"], api_key="test-key")

    # 2. Act
    # Call the tool function directly
    response = await stamp_status(req)

    # 3. Assert
    # Check that the service was called correctly
    mock_perform_status.assert_called_once_with(req, None, api_key="test-key")

    # Check that the response is structured correctly
    assert response.requestId == "unknown"
    assert len(response.data) == 1
    assert response.data[0].uid == "0x123"
    assert response.data[0].error == "Test error"
