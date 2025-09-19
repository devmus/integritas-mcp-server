# # src/integritas_mcp_server/stdio_app.py
# from integritas_mcp_server.logging_setup import setup_logging
# from integritas_mcp_server.tools import register_tools
# from mcp.server.fastmcp import FastMCP


# mcp = FastMCP("Integritas MCP Server")
# setup_logging()                 # ensure logs go to stderr
# register_tools(mcp)

# src/integritas_mcp_server/stdio_app.py
from integritas_mcp_server.logging_setup import setup_logging
from integritas_mcp_server.core import mcp

# Import side-effects: registers tools & resources on the shared mcp
from integritas_mcp_server import tools as _tools   # noqa: F401
from integritas_mcp_server import resources as _res # noqa: F401

def build_app():
    setup_logging()
    # If you used a separate register_tools() function, call it here:
    if hasattr(_tools, "register_tools"):
        _tools.register_tools()
    return mcp

# If your runner expects an `mcp` symbol:
mcp = build_app()
