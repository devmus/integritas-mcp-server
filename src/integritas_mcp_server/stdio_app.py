# src/integritas_mcp_server/stdio_app.py
from integritas_mcp_server.logging_setup import setup_logging
from integritas_mcp_server.core import mcp

# init logging when launched via "…/stdio_app.py:mcp"
setup_logging()

# Import side-effects: registers tools & resources on the shared mcp
from integritas_mcp_server import tools as _tools   # noqa: F401
from integritas_mcp_server import resources as _res # noqa: F401

def build_app():
    if hasattr(_tools, "register_tools"):
        _tools.register_tools()
    return mcp

mcp = build_app()