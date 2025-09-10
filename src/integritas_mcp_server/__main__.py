# # src/integritas_mcp_server/__main__.py

# import argparse
# import asyncio
# import sys
# from integritas_mcp_server.services.self_health import self_health

# def main():
#     p = argparse.ArgumentParser()
#     p.add_argument("--stdio", action="store_true")
#     p.add_argument("--health", action="store_true")
#     args = p.parse_args()

#     if args.health:
#         res = asyncio.run(self_health("integritas-cli-health"))
#         print(res.model_dump_json(indent=2))  # if you keep this, redirect to stderr in stdio mode
#         sys.exit(0 if res.status == "ok" and res.upstream_reachable else 1)

#     if args.stdio:
#         from .stdio_app import run_stdio_blocking
#         run_stdio_blocking()
#     else:
#         p.print_help()

# if __name__ == "__main__":
#     main()

# src/integritas_mcp_server/__main__.py
from .cli import run

if __name__ == "__main__":
    run()
