# # src\integritas_mcp_server\sse_app.py

# from __future__ import annotations
# from starlette.applications import Starlette
# from starlette.routing import Mount
# from .stdio_app import mcp

# # By default, SSE mounts at `/sse` inside the app; mounting at `/` exposes `/sse`
# app = Starlette(routes=[Mount("/", app=mcp.sse_app())])

from __future__ import annotations
from starlette.applications import Starlette
from starlette.routing import Mount

from .stdio_app import mcp
from .config import get_settings
from .security import BearerGuard

# Build the inner MCP SSE ASGI app
_inner = mcp.sse_app()

# Load secrets (MCP access token) from your config/env
_settings = get_settings()

# Wrap with bearer guard
_guarded = BearerGuard(_inner, _settings.mcp_access_token)

# Mount at "/" so the effective SSE path is "/sse" (as you’re already using)
app = Starlette(routes=[Mount("/", app=_guarded)])
