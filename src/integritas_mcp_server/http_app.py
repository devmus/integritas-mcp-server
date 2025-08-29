# src/integritas_mcp_server/http_app.py
from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from .models import StampRequest, StampResponse
from .errors import MCPServerError
from .services.stamp import stamp as stamp_service
from .config import get_settings
from .http_client import get_json
from integritas_mcp_server.services.health import check_readiness
from integritas_mcp_server.services.self_health import self_health

app = FastAPI(title="Integritas MCP Server – HTTP shim", version="0.1.0")

# --- Liveness: process is up
@app.get("/health")
async def healthz():
    return self_health().model_dump()

# --- Readiness: upstream reachable + auth works
@app.get("/tools/readyz")
async def readyz():
    return (await check_readiness(None)).model_dump()

# --- Tool: stamp
# @app.post("/tools/stamp", response_model=StampResponse)
# async def stamp(req: StampRequest, x_request_id: str | None = Header(default=None)):
@app.post("/tools/stamp", response_model=StampResponse)
async def stamp(req: StampRequest, x_request_id: str | None = Header(default=None)):
    try:
        # return await stamp_service(req.hash, x_request_id)
        
        # Prefer req.api_key if present; http shim does not itself read x-api-key
        return await stamp_service(req.hash, x_request_id, api_key=req.api_key)
    except MCPServerError as e:
        # Upstream said no (400/401/403/429/5xx mapped); present as a client error
        raise HTTPException(status_code=400, detail=str(e)) from e
