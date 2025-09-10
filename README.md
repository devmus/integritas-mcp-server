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

### Tools

- Stamp

0. Upload file
1. Hash file
2. Core API /post-lite
3. Core API /status
4. Return json proof
5. Core API /timestamp/file
6. Return json proof as file

- Verify

0. Upload proof file
1. Core API /verify-lite
2. Return verification result as json
3. Core API /verify/file
4. Return verification result as .pdf
