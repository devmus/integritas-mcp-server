# src/integritas_mcp_server/http_app.py
from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException
from .models import StampRequest, StampResponse
from .errors import MCPServerError
from .services.stamp import stamp as stamp_service
from .config import get_settings

app = FastAPI(title="Integritas MCP Server – HTTP shim", version="0.1.0")

# --- Liveness: process is up
@app.get("/tools/health")
async def health_tools():
    return {"status": "ok"}

# --- Readiness: upstream reachable + auth works

@app.get("/tools/readyz")
async def readyz():
    s = get_settings()
    try:
        # very lightweight upstream probe
        r = await get_json("/v1/web/check/health")   # or a cheap HEAD/GET you already trust
        ok = r.status_code < 300
    except Exception:
        ok = False

    return (
        {"status": "ok", "upstream": "ok"},
        200
    ) if ok else (
        {"status": "degraded", "upstream": "unreachable"},
        503
    )

@app.post("/tools/stamp", response_model=StampResponse)
async def stamp(req: StampRequest, x_request_id: str | None = Header(default=None)):
    try:
        return await stamp_service(req.hash, x_request_id)
    except MCPServerError as e:
        # Upstream said no (400/401/403/429/5xx mapped); present as a client error
        raise HTTPException(status_code=400, detail=str(e)) from e
