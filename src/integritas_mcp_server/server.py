# src/integritas_mcp_server/server.py
from typing import Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
import httpx, os
from config import settings
import structlog, sys

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)
log = structlog.get_logger()

API_BASE = settings.minima_api_base
API_KEY = settings.minima_api_key

log.info("Loaded config", api_base=API_BASE, api_key=API_KEY[:6] + "..." if API_KEY else None)

mcp = FastMCP("Integritas MCP Server")

class StampRequest(BaseModel):
    hash: str = Field(..., description="Hex or base64 hash")

class StampResponse(BaseModel):
    uid: str
    summary: str

@mcp.tool()
async def stamp_hash(req: StampRequest, ctx: Context) -> StampResponse:
    
    headers = {"x-api-key": f"{API_KEY}", "x-request-id": "integritas-mcp-server"} if API_KEY else {}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE}/v1/timestamp/post", json={"hash":req.hash}, headers=headers)
        r.raise_for_status()
        data = r.json()
        log.info("API response", response=data)
    return StampResponse(uid=data["data"]["uid"], summary=f"Submitted stamp for {req.hash}")


if __name__ == "__main__":
    mcp.run()
