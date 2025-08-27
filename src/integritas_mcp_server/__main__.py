# src/integritas_mcp_server/__main__.py

import argparse, asyncio, sys
from .services.health import check_health

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stdio", action="store_true")
    p.add_argument("--health", action="store_true")
    args = p.parse_args()

    if args.health:
        res = asyncio.run(check_health("integritas-cli-health"))
        print(res.model_dump_json(indent=2))
        sys.exit(0 if res.status == "ok" and res.upstream_reachable else 1)

    if args.stdio:
        from .server import serve_stdio
        asyncio.run(serve_stdio())
    else:
        p.print_help()

if __name__ == "__main__":
    main()
