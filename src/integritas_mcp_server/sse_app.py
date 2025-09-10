from __future__ import annotations
from starlette.applications import Starlette
from starlette.routing import Mount
from .stdio_app import mcp

# By default, SSE mounts at `/sse` inside the app; mounting at `/` exposes `/sse`
app = Starlette(routes=[Mount("/", app=mcp.sse_app())])
