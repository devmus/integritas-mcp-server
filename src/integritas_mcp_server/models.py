# src/integritas_mcp_server/models.py

from __future__ import annotations

"""
Data Transfer Objects used by the Integritas MCP server.

Design goals:
- Minimal, host-agnostic shapes
- One common ToolResult "envelope" for all tools
- All tool responses return: { requestId, summary, structuredContent }
- No business logic in models (validators are only for "one-of" input sanity)
"""

from typing import Optional, Dict, Any, List, Literal
from datetime import datetime, timezone

from pydantic import BaseModel, Field, AnyUrl, ConfigDict, model_validator

# ---------- Envelope constants ----------

STAMP_RESULT_KIND = "integritas/stamp_result@v1"
VERIFY_RESULT_KIND = "integritas/verify_result@v1"
SCHEMA_URI = "https://integritas.dev/schemas/tool-result-v1.json"

# ---------- Common UI primitives ----------

class ToolLink(BaseModel):
    """Renderable hyperlink (client renders <a>)."""
    rel: str                         # e.g. "proof", "verification", "download"
    href: AnyUrl
    label: Optional[str] = None


class ToolResultEnvelopeV1(BaseModel):
    """
    Versioned, provider-agnostic tool result container.
    All server tools should populate this and return it under `structuredContent`.
    """
    kind: str                                        # e.g. "integritas/stamp_result@v1"
    status: Optional[Literal["finalized", "pending", "failed", "unknown"]] = None
    summary: Optional[str] = None
    ids: Optional[Dict[str, str]] = None             # e.g. {"uid": "...", "tx_id": "..."}
    timestamps: Optional[Dict[str, str]] = None      # ISO-8601 UTC strings
    links: Optional[List[ToolLink]] = None           # buttons/anchors in the client
    data: Optional[Any] = None                       # raw domain payload (for copy/export)
    error: Optional[Dict[str, Any]] = None           # { code?, message, details? }
    schema_uri: Optional[str] = Field(default=SCHEMA_URI, alias="$schema")

    model_config = ConfigDict(populate_by_name=True)

# ---------- Common tool response ----------

class ToolResponse(BaseModel):
    """
    Standard tool response returned by all MCP tools.
    - `summary` is plain human-readable text (for the chat transcript)
    - `structuredContent` is the versioned envelope above
    """
    requestId: str
    summary: Optional[str] = None
    structuredContent: ToolResultEnvelopeV1


# Keep specific class names for clarity/imports, but they’re identical.
class StampDataResponse(ToolResponse): ...
class VerifyDataResponse(ToolResponse): ...


# ---------- Requests ----------

class StampDataRequest(BaseModel):
    """
    Stamp a file or a precomputed hash.
    Provide exactly one of:
      - file_hash  (preferred if you already computed it)
      - file_url   (server downloads and stamps)
      - file_path  (server reads local path and stamps)
    """
    file_hash: Optional[str] = None
    file_url: Optional[AnyUrl] = None
    file_path: Optional[str] = None
    api_key: Optional[str] = None  # forwarded to upstream if set

    @model_validator(mode="after")
    def _one_of(self):
        if not (self.file_hash or self.file_url or self.file_path):
            raise ValueError("Provide one of file_hash, file_url, or file_path.")
        return self


class VerifyDataRequest(BaseModel):
    """
    Verify a proof file (JSON) from a URL or local path.
    Provide one of:
      - file_url
      - file_path
    """
    file_url: Optional[AnyUrl] = None
    file_path: Optional[str] = None
    api_key: Optional[str] = None  # forwarded to upstream if set

    @model_validator(mode="after")
    def _one_of(self):
        if not (self.file_url or self.file_path):
            raise ValueError("Provide file_url or file_path.")
        return self


# ---------- Health (optional but handy) ----------

class HealthResponse(BaseModel):
    """Simple health probe DTO; useful for readiness/liveness checks."""
    status: Literal["ok", "degraded", "down"] = "ok"
    server: str = "Integritas MCP Server"
    version: str = "0.1.0"
    time_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    upstream_reachable: bool = True
    upstream_status: Optional[int] = None
    upstream_latency_ms: Optional[int] = None
    summary: str = "Healthy"