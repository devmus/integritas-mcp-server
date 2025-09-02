# src\integritas_mcp_server\services\self_health.py

from __future__ import annotations
import os
import time
from pydantic import BaseModel

_PROCESS_START = time.time()

class SelfHealth(BaseModel):
    status: str  # "ok"
    summary: str
    pid: int
    uptime_s: int
    version: str | None = None

def self_health(version: str | None = None) -> SelfHealth:
    return SelfHealth(
        status="ok",
        summary="MCP server is alive",
        pid=os.getpid(),
        uptime_s=int(time.time() - _PROCESS_START),
        version=version,
    )
