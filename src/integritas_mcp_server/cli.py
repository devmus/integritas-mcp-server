# src/integritas_mcp_server/cli.py
from __future__ import annotations
import os, sys, typer, uvicorn
from .logging_setup import setup_logging

cli = typer.Typer(no_args_is_help=True, add_completion=False)

@cli.command("stdio")
def cmd_stdio():
    """
    Start the MCP server over stdio. Compatible with FastMCP.run_stdio() and FastMCP.run().
    """
    setup_logging()

    # Lazy import so logging is configured first and to avoid pulling in the whole
    # server when running other subcommands like `http` or `sse`.
    from .stdio_app import mcp  # registers tools/resources on import

    # Compatibility shim: some versions expose run_stdio(), others run()
    run_stdio = getattr(mcp, "run_stdio", None)
    if callable(run_stdio):
        run_stdio()
        return

    run = getattr(mcp, "run", None)
    if callable(run):
        run()
        return

    # Fallback if API changed
    raise RuntimeError("FastMCP instance has neither run_stdio() nor run().")

@cli.command("sse")
def cmd_sse(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
):
    setup_logging()
    from .config import get_settings
    s = get_settings()
    from .sse_app import app as sse_asgi_app
    uvicorn.run(
        sse_asgi_app,
        host=host,
        port=port,
        reload=reload,
        log_level=s.log_level.lower(),
    )

@cli.command("http")
def cmd_http(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
):
    setup_logging()
    from .config import get_settings
    s = get_settings()
    from .http_app import app as http_asgi_app
    uvicorn.run(
        http_asgi_app,
        host=host,
        port=port,
        reload=reload,
        log_level=s.log_level.lower(),
    )

def run():
    cli()

if __name__ == "__main__":
    run()
