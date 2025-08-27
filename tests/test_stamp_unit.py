# tests/test_stamp_unit.py
import respx
import httpx
import pytest
from integritas_mcp_server.server import stamp_hash
from integritas_mcp_server.models import StampRequest

@pytest.mark.anyio("asyncio")
@respx.mock
async def test_stamp_success():
    respx.post("https://upstream.example/v1/timestamp/post").mock(
        return_value=httpx.Response(200, json={"uid":"u123","tx_id":"t456","stamped_at":"2025-08-26T10:00:00Z"})
    )
    resp = await stamp_hash(StampRequest(hash="aabb"))
    assert resp.uid == "u123"
    assert "Stamp accepted" in resp.summary

@pytest.mark.anyio("asyncio")
@respx.mock
async def test_upstream_400_maps_to_invalid():
    respx.post("https://upstream.example/v1/timestamp/post").mock(
        return_value=httpx.Response(400, text="bad hash")
    )
    with pytest.raises(Exception) as ei:
        await stamp_hash(StampRequest(hash="zz=="))  # invalid base64 → model normalizes, but upstream rejects
    assert "bad hash" in str(ei.value)
