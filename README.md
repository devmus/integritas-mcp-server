## Integritas MCP Server (stamp-only)

### Configure

MINIMA_API_BASE=https://your-upstream.example

MINIMA_API_KEY=... # optional

### Run (MCP stdio)

integritas-mcp stdio

### Run (HTTP shim for dev)

integritas-mcp http --host 0.0.0.0 --port 8787

### Test

pytest -q

### Generate schemas

python scripts/generate_schemas.py

### Hash request
