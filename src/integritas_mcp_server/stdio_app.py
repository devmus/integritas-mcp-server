# from __future__ import annotations
# from mcp.server.fastmcp import FastMCP
# from integritas_mcp_server.tools import register_tools

# # One FastMCP app
# mcp = FastMCP("Integritas MCP Server")
# register_tools(mcp)

# def run_stdio_blocking() -> None:
#     # DO NOT wrap with asyncio.run — FastMCP manages the loop
#     mcp.run()


# src/integritas_mcp_server/stdio_app.py
from integritas_mcp_server.logging_setup import setup_logging
from integritas_mcp_server.tools import register_tools
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Integritas MCP Server")
setup_logging()                 # ensure logs go to stderr
register_tools(mcp)