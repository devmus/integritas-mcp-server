# integritas_mcp/resources.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel
from mcp.server.fastmcp import Context
from integritas_mcp_server.core import mcp


# ----------------------------
# 0) Helper: ISO UTC timestamp
# ----------------------------
def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

# --------------------------------
# 1) Static Markdown documentation
# --------------------------------
_OVERVIEW_MD = """# Integritas — Minima stamping

Integritas provides cryptographic timestamping on the Minima blockchain
and portable proof bundles you can verify anywhere.

## What this MCP server offers
- **Stamp** a content hash or file (one-shot).
- **Verify** a hash or a proof bundle.
- **Status** lookups by `uid` or `tx_id`.
- **Resolve proof** bundle from a known reference.

All timestamps are UTC ISO-8601. Hashes are normalized to lowercase hex.
"""

_FAQ_MD = """# Integritas FAQ

**What is stamped?**  
A normalized content hash (or a hash of your uploaded file).

**How do I verify?**  
Either supply a hash for on-chain lookup or provide a proof bundle.

**What do `uid` and `tx_id` mean?**  
`uid` is your Integritas reference; `tx_id` is the Minima transaction id.

**Is an API key required?**  
Depends on your upstream policy; include `api_key` when needed.
"""

@mcp.resource("integritas://docs/overview", mime_type="text/markdown")
def docs_overview() -> str:
    """Integritas product overview (Markdown)"""
    return _OVERVIEW_MD

@mcp.resource("integritas://docs/faq", mime_type="text/markdown")
def docs_faq() -> str:
    """Frequently asked questions (Markdown)"""
    return _FAQ_MD

# -------------------------------------------------------
# 2) Dynamic tool catalog (Markdown) from your own models
# -------------------------------------------------------
# You likely already have Pydantic models for inputs/outputs:
# e.g., StampRequest, StampResponse, VerifyRequest, VerifyResponse, etc.
# Import them here and register them below.
try:
    from .models import (
        StampDataRequest, StampDataResponse,
        VerifyDataRequest, VerifyDataResponse,
    )
except Exception:
    # Fallback stubs if imports aren’t ready yet
    class StampDataRequest(BaseModel): hash: Optional[str] = None
    class StampDataResponse(BaseModel): status: str
    class VerifyDataRequest(BaseModel): hash: Optional[str] = None
    class VerifyDataResponse(BaseModel): is_valid: bool

TOOL_REGISTRY: list[dict[str, Any]] = [
    {
        "name": "stamp.v1",
        "title": "Stamp content",
        "description": "Stamp a precomputed hash or file (URL/path).",
        "input_model": StampDataRequest,
        "output_model": StampDataResponse,
        "examples": [
            {"hash": "4f48…34998"},
            {"file_url": "https://example.com/file.pdf"}
        ],
    },
    {
        "name": "verify.v1",
        "title": "Verify hash or proof bundle",
        "description": "Check on-chain or validate a provided proof file.",
        "input_model": VerifyDataRequest,
        "output_model": VerifyDataResponse,
        "examples": [
            {"hash": "82884d9b…6190ff"},
            {"proof_url": "https://example.com/proof.json"}
        ],
    },
]

def _render_tools_markdown() -> str:
    lines: list[str] = ["# Integritas MCP — Tools", ""]
    for tool in TOOL_REGISTRY:
        in_schema = tool["input_model"].model_json_schema()
        out_schema = tool["output_model"].model_json_schema()
        lines += [
            f"## `{tool['name']}` — {tool['title']}",
            "",
            tool["description"],
            "",
            "### Input schema",
            "```json",
            __import__("json").dumps(in_schema, indent=2),
            "```",
            "### Output schema",
            "```json",
            __import__("json").dumps(out_schema, indent=2),
            "```",
        ]
        if ex := tool.get("examples"):
            lines += ["### Examples", "```json",
                      __import__("json").dumps(ex, indent=2),
                      "```"]
        lines.append("")
    return "\n".join(lines)

@mcp.resource("integritas://docs/tools", mime_type="text/markdown")
def docs_tools_catalog() -> str:
    """Human-readable catalog of tools with schemas/examples"""
    return _render_tools_markdown()

# ------------------------------------------------------
# 3) Schema template: integritas://schema/{name} (JSON)
# ------------------------------------------------------
# Expose JSON schema for any known model name
_SCHEMA_INDEX: dict[str, type[BaseModel]] = {
    "stamp_input": StampDataRequest,
    "stamp_output": StampDataResponse,
    "verify_input": VerifyDataRequest,
    "verify_output": VerifyDataResponse
}

@mcp.resource("integritas://schema/{name}", mime_type="application/json")
def schema_by_name(name: str) -> dict:
    """JSON Schema for inputs/outputs (e.g., schema/stamp_input)"""
    model = _SCHEMA_INDEX.get(name)
    if not model:
        return {"error": {"code": "NOT_FOUND", "message": f"Unknown schema '{name}'"}}
    return {
        "name": name,
        "lastModified": iso_now(),
        "schema": model.model_json_schema(),
    }

# -----------------------------------------
# 4) Server info: integritas://server/info
# -----------------------------------------
@mcp.resource("integritas://server/info", mime_type="application/json")
def server_info() -> dict[str, Any]:
    toolset_version = "v1"
    api_version = "2025-09-01"
    build_sha = "unknown"

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    return {
        "name": "Integritas MCP Server",
        "toolset_version": toolset_version,
        "api_version": api_version,
        "build_sha": build_sha,
        "now": now,
        # request_id omitted because no context here
        "tools": [t["name"] for t in TOOL_REGISTRY],
    }
