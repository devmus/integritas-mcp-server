# src/integritas_mcp_server/server.py
from __future__ import annotations
from typing import Optional
from mcp.server.fastmcp import FastMCP, Context
import structlog
from .models import StampRequest, StampResponse
from .services.stamp import stamp as stamp_service

log = structlog.get_logger()
mcp = FastMCP("Integritas MCP Server")

@mcp.tool()
async def stamp_hash(req: StampRequest, ctx: Optional[Context] = None) -> StampResponse:
    """
    Stamp a content hash on the Minima blockchain.
    Input:
      - hash: Hex (with/without 0x) or base64 string. Will be normalized to lowercase hex.
    Output:
      - uid, tx_id, stamped_at, summary
    """
    req_id = getattr(ctx, "request_id", None) if ctx is not None else None
    return await stamp_service(req.hash, req_id)

# Convenience for various SDK versions
async def serve_stdio():
    try:
        await mcp.run_stdio()
    except AttributeError:
        await mcp.run()
