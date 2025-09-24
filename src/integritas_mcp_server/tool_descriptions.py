# src\integritas_mcp_server\tool_descriptions.py
HEALTH_DESCRIPTION = """
Liveness: quick, in-process check (no network).
"""

READY_DESCRIPTION = """
Readiness probe: checks downstream Integritas API reachability and auth.
Accepts optional api_key to test authenticated calls.
"""

STAMP_DATA_DESCRIPTION = """
Stamp a file or a hash on the Minima blockchain via Integritas one-shot API.

Input (provide exactly one):
  - file_hash: sha3-256 (preferred if already computed)
  - file_url: Presigned URL
  - file_path: Server-accessible local path

Output:
  - summary: Plain, human-readable summary.
  - structuredContent (ToolResultEnvelopeV1):
      kind: "integritas/stamp_result@v1"
      status: "pending" | "finalized" | "failed" | "unknown"
      ids: { uid? }
      timestamps: { stamped_at? }
      links: [{ rel: "proof", href: <url>, label?: "Download proof" }]
      data: raw domain payload (may include status, uid, stamped_at, proof_url)
      $schema: "https://integritas.dev/schemas/tool-result-v1.json"
"""

VERIFY_DATA_DESCRIPTION = """
Verify a proof file against the Minima blockchain via Integritas one-shot API.

Input (provide one):
  - file_url: Presigned URL (recommended)
  - file_path: Server-accessible local path

Output:
  - summary: Plain, human-readable summary.
  - structuredContent (ToolResultEnvelopeV1):
      kind: "integritas/verify_result@v1"
      status: "finalized" | "pending" | "failed" | "unknown"
      ids: { tx_id?, txpow_id?, uid?, matched_hash? }
      timestamps: { verified_at, block_number? }
      links: [{ rel: "verification", href: <url>, label?: "View verification" }]
      data: raw domain payload (may include result, block_number, etc.)
      $schema: "https://integritas.dev/schemas/tool-result-v1.json"
"""
