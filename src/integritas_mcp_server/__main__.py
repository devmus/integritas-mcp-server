# src/integritas_mcp_server/__main__.py

import argparse, asyncio, sys
from integritas_mcp_server.services.self_health import self_health

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stdio", action="store_true")
    p.add_argument("--health", action="store_true")
    args = p.parse_args()

    if args.health:
        res = asyncio.run(self_health("integritas-cli-health"))
        print(res.model_dump_json(indent=2))  # if you keep this, redirect to stderr in stdio mode
        sys.exit(0 if res.status == "ok" and res.upstream_reachable else 1)

    if args.stdio:
        # ⬇️ call the FastMCP instance directly (no serve_stdio import)
        from .server import mcp
        asyncio.run(mcp.run())
    else:
        p.print_help()

if __name__ == "__main__":
    main()