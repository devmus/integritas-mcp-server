# src/integritas_mcp_server/http_app.py
from __future__ import annotations
from fastapi import FastAPI, Header, Request, HTTPException, APIRouter
from .models import StampRequest, StampResponse, StampStatusRequest, StampStatusResponse
from .errors import MCPServerError
from .services.stamp import stamp as stamp_service
from .services.stamp_status import perform_stamp_status
from integritas_mcp_server.services.health import check_readiness
from integritas_mcp_server.services.self_health import self_health
from .models import HealthResponse
from typing import Optional

app = FastAPI(title="Integritas MCP Server – HTTP shim", version="0.1.0")

# Create routers for different API sections
tools_router = APIRouter()
v1_router = APIRouter()

# --- Liveness: process is up
@app.get("/health")
async def healthz():
    return self_health().model_dump()

# --- Readiness: upstream reachable + auth works
@tools_router.get("/readyz", response_model=HealthResponse)
async def readyz(
    request: Request,
    x_request_id: Optional[str] = Header(default=None, alias="x-request-id"),
    x_api_key: Optional[str]   = Header(default=None, alias="x-api-key")
):
    return await check_readiness(
        x_request_id=x_request_id,
        api_key=x_api_key,             # <-- forward it!
    )

# --- Tool: stamp
@v1_router.post("/timestamp/post", response_model=StampResponse)
async def stamp(req: StampRequest, x_request_id: str | None = Header(default=None), x_api_key: Optional[str]   = Header(default=None, alias="x-api-key")):
    try:
        # Prefer req.api_key if present; http shim does not itself read x-api-key
        return await stamp_service(req.hash, x_request_id, api_key=x_api_key)
    except MCPServerError as e:
        # Upstream said no (400/401/403/429/5xx mapped); present as a client error
        raise HTTPException(status_code=400, detail=str(e)) from e

@v1_router.post("/timestamp/status", response_model=StampStatusResponse)
async def stamp_status(
    req: StampStatusRequest,
    x_request_id: Optional[str] = Header(default=None, alias="x-request-id"),
    x_api_key: Optional[str] = Header(default=None, alias="x-api-key"),
):
    try:
        results = await perform_stamp_status(req, x_request_id, x_api_key)
        return StampStatusResponse(
            requestId=x_request_id or "unknown",
            data=results,
        )
    except MCPServerError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

# Include the routers in the main app
app.include_router(tools_router, prefix="/tools")
app.include_router(v1_router, prefix="/v1")
