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

{"hash":"4f481c90915e8a96fd8426e541d83dc547b573dd7a83fb2f4dcb4a77e5234998"}
