# # src\integritas_mcp_server\cli.py
from __future__ import annotations
import typer, uvicorn
from .config import get_settings
from .logging_setup import setup_logging
from .sse_app import app as sse_asgi_app
from .http_app import app as http_asgi_app
from .stdio_app import mcp

cli = typer.Typer(no_args_is_help=True, add_completion=False)

# @cli.command("stdio")
# def cmd_stdio():
#     run_stdio_blocking()  # <- no asyncio.run

@cli.command("stdio")
def cmd_stdio():
    
    mcp.run()

@cli.command("sse")
def cmd_sse(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
):
    setup_logging()
    s = get_settings()
    uvicorn.run(sse_asgi_app, host=host, port=port, reload=reload, log_level=s.log_level.lower())

@cli.command("http")
def cmd_http(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
):
    setup_logging()
    s = get_settings()
    uvicorn.run(http_asgi_app, host=host, port=port, reload=reload, log_level=s.log_level.lower())

def run():
    cli()
