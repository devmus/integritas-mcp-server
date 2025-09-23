# src\integritas_mcp_server\tools.py
# from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from mcp.server.fastmcp import Context
from integritas_mcp_server.core import mcp

from .models import (
    StampDataRequest, StampDataResponse,
    VerifyDataRequest, VerifyDataResponse,
)

from .services.stamp_data import stamp_data_complete
from .services.verify_data import verify_data_complete
from .services.self_health import self_health
from .services.health import check_readiness
from .tool_descriptions import (
    HEALTH_DESCRIPTION, READY_DESCRIPTION,
    STAMP_DATA_DESCRIPTION,
    VERIFY_DATA_DESCRIPTION
)
from .logging_utils import tool_logger
from .logging_setup import get_logger

log = get_logger()

class ReadyRequest(BaseModel):
    api_key: str | None = None

def register_tools() -> None:
    @tool_logger
    @mcp.tool()
    async def health() -> dict:
        return self_health(version=None).model_dump()
    health.__doc__ = HEALTH_DESCRIPTION

    @tool_logger
    @mcp.tool()
    async def ready(req: ReadyRequest, ctx: Optional[Context] = None) -> dict:
        req_id = getattr(ctx, "request_id", None) if ctx else None
        return await check_readiness(x_request_id=req_id, api_key=req.api_key)
    ready.__doc__ = READY_DESCRIPTION

    @tool_logger
    @mcp.tool(name="stamp_data")
    async def stamp_data(req: StampDataRequest, ctx: Optional[Context] = None) -> StampDataResponse:
        req_id = getattr(ctx, "request_id", None) if ctx else None
        return await stamp_data_complete(req, req_id, api_key=req.api_key)
    stamp_data.__doc__ = STAMP_DATA_DESCRIPTION

    @tool_logger
    @mcp.tool(name="verify_data")
    async def verify_data(req: VerifyDataRequest, ctx: Optional[Context] = None) -> VerifyDataResponse:
        req_id = getattr(ctx, "request_id", None) if ctx else None
        return await verify_data_complete(req, req_id, api_key=req.api_key)
    verify_data.__doc__ = VERIFY_DATA_DESCRIPTION

    # @mcp.tool(name="stamp_hash")
    # async def stamp_hash(req: StampRequest, ctx: Optional[Context] = None) -> StampResponse:
    #     req_id = getattr(ctx, "request_id", None) if ctx else None
    #     return await stamp_service(req.hash, req_id, api_key=req.api_key)
    # stamp_hash.__doc__ = STAMP_HASH_DESCRIPTION

    # @mcp.tool(name="get_stamp_status")
    # async def get_stamp_status(req: StampStatusRequest, ctx: Optional[Context] = None) -> StampStatusResponse:
    #     req_id = getattr(ctx, "request_id", None) if ctx else None
    #     results = await get_definitive_stamp_status(req, req_id, api_key=req.api_key)
    #     return StampStatusResponse(requestId=req_id or "unknown", data=results)
    # get_stamp_status.__doc__ = STAMP_STATUS_DESCRIPTION
