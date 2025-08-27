# src/integritas_mcp_server/models.py

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
import base64, re
from typing import Literal, Optional
from datetime import datetime, timezone

HEX_RE = re.compile(r"^(0x)?[0-9a-fA-F]+$")

def _b64_to_hex(s: str) -> str:
    try:
        raw = base64.b64decode(s, validate=True)
    except Exception as e:  # noqa: BLE001
        raise ValueError("Invalid base64 hash") from e
    return raw.hex()

def normalize_hash(value: str) -> str:
    v = value.strip()
    if HEX_RE.match(v):
        v = v[2:] if v.lower().startswith("0x") else v
        return v.lower()
    # try base64 → hex
    return _b64_to_hex(v).lower()

class StampRequest(BaseModel):
    hash: str = Field(..., description="Hex (with/without 0x) or base64; will be normalized to hex.")

    @field_validator("hash")
    @classmethod
    def _normalize(cls, v: str) -> str:
        return normalize_hash(v)

class StampResponse(BaseModel):
    uid: str = Field(..., description="Server-side UID correlating to the stamp operation.")
    stamped_at: str | None = Field(None, description="ISO-8601 UTC timestamp when accepted.")
    summary: str = Field(..., description="Human-readable summary of the result.")

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"] = "ok"
    server: str = "Integritas MCP Server"
    version: str = "0.1.0"
    time_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    upstream_reachable: bool = True
    upstream_status: Optional[int] = None
    upstream_latency_ms: Optional[int] = None
    summary: str = "Healthy"