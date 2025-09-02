# src/integritas_mcp_server/server.py
from __future__ import annotations
import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP, Context
from integritas_mcp_server.models import StampRequest, StampResponse, StampStatusRequest, StampStatusResponse
from integritas_mcp_server.services.stamp import stamp as stamp_service
from integritas_mcp_server.services.stamp_status import get_definitive_stamp_status
from integritas_mcp_server.services.self_health import self_health
from integritas_mcp_server.services.health import check_readiness
from pydantic import BaseModel
import structlog

structlog.configure(
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr)  # force stderr
)

log = structlog.get_logger()
mcp = FastMCP("Integritas MCP Server")

class ReadyRequest(BaseModel):
    api_key: str | None = None

@mcp.tool()
async def health() -> dict:
    """
    Liveness: quick, in-process check (no network).
    """
    # If you track a version in settings, pass it here; else None
    res = self_health(version=None)
    return res.model_dump()

@mcp.tool()
async def ready(req: ReadyRequest, ctx=None) -> dict:
    """
    Input:
    - Integritas Api key
    
    Input Schema:
    {"api_key":"your-api-key"}
    """
    req_id = getattr(ctx, "request_id", None) if ctx else None
    res = await check_readiness(req_id, api_key=req.api_key)
    return res.model_dump()

@mcp.tool()
# async def stamp_hash(req: StampRequest, ctx: Optional[Context] = None) -> StampResponse:
async def stamp_hash(req: StampRequest, ctx: Optional[Context] = None) -> StampResponse:
    """
    Stamp a content hash on the Minima blockchain.
    Input:
      - hash: Hex (with/without 0x) or base64 string. Will be normalized to lowercase hex.
      - Integritas Api key
      Input Schema:
      {"hash":"4f481c90915e8a96fd8426e541d83dc547b573dd7a83fb2f4dcb4a77e5234998", "api_key":"your-api-key"}
    Output:
      - uid, stamped_at, summary
    """
    req_id = getattr(ctx, "request_id", None) if ctx is not None else None
    # return await stamp_service(req.hash, req_id)
    return await stamp_service(req.hash, req_id, api_key=req.api_key)

@mcp.tool()
async def stamp_status(req: StampStatusRequest, ctx: Optional[Context] = None) -> StampStatusResponse:
    """
    Checks the blockchain transaction status for a list of UIDs.
    Input:
      - uids: A list of UIDs to check.
      - api_key: Optional API key.
    Input Schema:
      {"uids":["0x..."], "api_key":"your-api-key"}
    Output:
      - The full status response object.
    """
    req_id = getattr(ctx, "request_id", None) if ctx is not None else None
    results = await get_definitive_stamp_status(req, req_id, api_key=req.api_key)
    return StampStatusResponse(
        requestId=req_id or "unknown",
        data=results,
    )