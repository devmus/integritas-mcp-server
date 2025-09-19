# src/integritas_mcp_server/core.py
from mcp.server.fastmcp import FastMCP

# Keep this module tiny to avoid import side effects
mcp = FastMCP("Integritas MCP Server")
