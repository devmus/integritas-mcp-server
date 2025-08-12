# src/integritas_mcp_server/server.py
from typing import Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
import httpx, os

API_BASE = os.getenv("MINIMA_API_BASE", "https://your-api.example.com")
API_KEY = os.getenv("MINIMA_API_KEY", "")

mcp = FastMCP("Integritas MCP Server")

class StampRequest(BaseModel):
    hash: str = Field(..., description="Hex or base64 hash")

class StampResult(BaseModel):
    uid: str
    tx_id: Optional[str] = None
    summary: str

@mcp.tool()
async def stamp_hash(req: StampRequest, ctx: Context) -> StampResult:
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE}/stamp", json={"hash": req.hash}, headers=headers)
        r.raise_for_status()
        data = r.json()
    return StampResult(uid=data["uid"], tx_id=data.get("tx_id"), summary=f"Submitted stamp for {req.hash}")

if __name__ == "__main__":
    mcp.run()
