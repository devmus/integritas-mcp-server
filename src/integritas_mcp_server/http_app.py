# # src\integritas_mcp_server\http_app.py

# from __future__ import annotations
# from starlette.applications import Starlette
# from starlette.routing import Mount
# from .stdio_app import mcp

# # By default this exposes endpoints under `/mcp`
# app = Starlette(routes=[Mount("/", app=mcp.streamable_http_app())])

# src/integritas_mcp_server/http_app.py
from __future__ import annotations
from .stdio_app import mcp

# Use the MCP streamable HTTP app directly (top-level),
# it exposes its own /mcp endpoint.
app = mcp.streamable_http_app()
