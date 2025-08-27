# src/integritas_mcp_server/http_app.py
from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from .models import StampRequest, StampResponse
from .errors import MCPServerError
from .services.stamp import stamp as stamp_service
from .config import get_settings
from .http_client import get_json

app = FastAPI(title="Integritas MCP Server – HTTP shim", version="0.1.0")

# --- Liveness: process is up
@app.get("/health")
async def health():
    return {"status": "ok"}

# --- Readiness: upstream reachable + auth works
@app.get("/tools/readyz")
async def readyz(x_request_id: str | None = Header(default=None)):
    s = get_settings()
    try:
        r = await get_json("/v1/web/check/health", x_request_id=x_request_id)
        ok = r.status_code < 300
    except Exception:
        ok = False

    if ok:
        return JSONResponse(status_code=200, content={
            "status": "ok",
            "upstream": "ok",
            "service": "integritas-mcp-server",
            "version": app.version,
        })
    else:
        return JSONResponse(status_code=503, content={
            "status": "degraded",
            "upstream": "unreachable",
            "service": "integritas-mcp-server",
            "version": app.version,
        })

# --- Tool: stamp
@app.post("/tools/stamp", response_model=StampResponse)
async def stamp(req: StampRequest, x_request_id: str | None = Header(default=None)):
    try:
        return await stamp_service(req.hash, x_request_id)
    except MCPServerError as e:
        # Upstream said no (400/401/403/429/5xx mapped); present as a client error
        raise HTTPException(status_code=400, detail=str(e)) from e
