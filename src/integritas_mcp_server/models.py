# src/integritas_mcp_server/models.py

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
import base64
import re
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl, model_validator, AnyUrl

VerifyErrorCode = Literal[
    "PROOF_URL_404",
    "PROOF_URL_UNREACHABLE",
    "PROOF_TIMEOUT",
    "PROOF_BAD_JSON",
    "CHAIN_NOT_FOUND",
    "CHAIN_UNREACHABLE",
    "CHAIN_TIMEOUT",
    "UNEXPECTED_STATUS",
    "UNKNOWN",
]

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
    api_key: str | None = Field(
        default=None,
        description="Per-request API key for upstream stamping API (overrides env key if provided).",
        )

    @field_validator("hash")
    @classmethod
    def _normalize(cls, v: str) -> str:
        return normalize_hash(v)

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"] = "ok"
    server: str = "Integritas MCP Server"
    version: str = "0.1.0"
    time_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    upstream_reachable: bool = True
    upstream_status: Optional[int] = None
    upstream_latency_ms: Optional[int] = None
    summary: str = "Healthy"

class ToolLink(BaseModel):
    rel: str                                  # e.g. "proof", "verification", "download"
    href: AnyUrl
    label: Optional[str] = None

class ToolResultEnvelopeV1(BaseModel):
    kind: str = Field(..., example="integritas/verify_result@v1")
    status: Optional[str] = Field(None, example="finalized")  # "finalized" | "pending" | "failed" | "unknown"
    summary: Optional[str] = None
    ids: Optional[Dict[str, str]] = None                      # e.g. {"tx_id": "...", "uid": "..."}
    timestamps: Optional[Dict[str, str]] = None               # ISO-8601 UTC
    links: Optional[List[ToolLink]] = None                    # renderable anchors
    data: Optional[Any] = None                                # raw domain payload
    error: Optional[Dict[str, Any]] = None                    # {code, message, details}
    schemaURI: Optional[str] = Field(None, alias="$schema")     # schema URI if you want

    class Config:
        populate_by_name = True

class StampDataRequest(BaseModel):
    """Request to stamp a file on the blockchain."""
    file_path: Optional[str] = Field(None, description="Path to the file to be stamped. Will be uploaded as multipart/form-data.")
    file_url: Optional[HttpUrl] = Field(None, description="Presigned URL to download the file.")
    file_hash: Optional[str] = Field(None, description="File hash.")
    api_key: Optional[str] = Field(None, description="Integritas API key (optional, may also be set globally).")

    # @model_validator(mode="after")
    # def ensure_source(self):
    #     if not self.file_path and not self.file_url:
    #         raise ValueError("Either file_path or file_url is required.")
    #     return self

class StampDataResponse(BaseModel):
    """Response containing results of a completed stamp request."""
    # requestId: str = Field(..., description="MCP request id, for tracing/debugging.")
    # status: str = Field(..., description="Status of the stamp request: pending, finalized, or failed.")
    # uid: Optional[str] = Field(None, description="Unique identifier of the stamp request in the backend.")
    # stamped_at: Optional[datetime] = Field(None, description="UTC timestamp when stamp was finalized.")
    # proof_url: Optional[HttpUrl] = Field(None, description="Link to the downloadable proof file.")
    # summary: Optional[str] = Field(None, description="Human-readable summary of the operation.")
    requestId: str
    summary: Optional[str] = None
    structuredContent: Optional[ToolResultEnvelopeV1] = None

    # --- legacy (optional for transition/back-compat) ---
    status: Optional[str] = None
    uid: Optional[str] = None
    stamped_at: Optional[datetime] = None
    proof_url: Optional[AnyUrl] = None

class VerifyError(BaseModel):
    code: VerifyErrorCode
    message: str
    context: Optional[Dict[str, Any]] = None

class VerifyDataRequest(BaseModel):
    """Request to stamp a file on the blockchain."""
    file_path: Optional[str] = Field(None, description="Path to the file to be stamped. Will be uploaded as multipart/form-data.")
    file_url: Optional[HttpUrl] = Field(None, description="Presigned URL to download the file.")
    api_key: Optional[str] = Field(None, description="Integritas API key (optional, may also be set globally).")

class VerifyDataResponse(BaseModel):
    """Response containing results of a completed verification request."""
    requestId: str
    summary: Optional[str] = None
    structuredContent: Optional[ToolResultEnvelopeV1] = None

    # --- legacy fields now OPTIONAL (kept for transition/back-compat) ---
    result: Optional[str] = None
    block_number: Optional[int] = None
    txpow_id: Optional[str] = None
    transactionid: Optional[str] = None
    matched_hash: Optional[str] = None
    nfttxnid: Optional[str] = None
    verification_url: Optional[AnyUrl] = None



# class StampResponse(BaseModel):
#     uid: str = Field(..., description="Server-side UID correlating to the stamp operation.")
#     stamped_at: str | None = Field(None, description="ISO-8601 UTC timestamp when accepted.")
#     summary: str = Field(..., description="Human-readable summary of the result.")


# class StampStatusRequest(BaseModel):
#     uids: list[str] = Field(..., description="A list of UIDs to check the status of.")
#     api_key: str | None = Field(
#         default=None,
#         description="Per-request API key for upstream stamping API (overrides env key if provided).",
#     )


# class StampStatusResultError(BaseModel):
#     status: Literal[False] = False
#     uid: str
#     error: str


# class StampStatusResultPending(BaseModel):
#     status: Literal[True] = True
#     uid: str
#     data: str
#     number: int
#     datecreated: str
#     onchain: Literal[False] = False


# class StampStatusResultSuccess(BaseModel):
#     status: Literal[True] = True
#     uid: str
#     data: str
#     number: int
#     datecreated: str
#     datestamped: str
#     root: str
#     proof: str
#     address: str
#     onchain: Literal[True] = True


# StampStatusResult = Union[StampStatusResultSuccess, StampStatusResultPending, StampStatusResultError]


# class StampStatusResponse(BaseModel):
#     apiVersion: int = 1
#     requestId: str
#     status: str = "success"
#     statusCode: int = 200
#     message: str = "UID statuses fetched"
#     timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
#     data: list[StampStatusResult]