# src/integritas_mcp_server/cli.py
from __future__ import annotations
import asyncio
import os
import typer
import uvicorn
from .stdio_app import mcp                 # ⬅️ import the FastMCP instance
from .http_app import app as http_app
from .config import get_settings
from .logging_setup import setup_logging

cli = typer.Typer(no_args_is_help=True, add_completion=False)

@cli.command("stdio")
def cmd_stdio():
    """Run as an MCP stdio server."""
    # Minimal and version-safe: FastMCP.run() is present across versions
    asyncio.run(mcp.run())

@cli.command("http")
def cmd_http(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
):
    """Run a small HTTP shim for local integration & tests."""
    setup_logging()
    s = get_settings()
    os.environ.setdefault("UVICORN_WORKERS", "1")
    uvicorn.run(http_app, host=host, port=port, reload=reload, log_level=s.log_level.lower())

def run():
    cli()
