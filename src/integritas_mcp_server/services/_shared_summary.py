# src/integritas_mcp_server/services/_shared_summary.py
from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, timezone

def utc_iso(dt: Optional[datetime] = None) -> str:
    """ISO-8601 in UTC with Z suffix."""
    return (dt or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")

def normalize_status(s: str | None) -> str:
    s = (s or "").lower().strip()
    if s in {"success", "ok", "done", "finalized"}:
        return "finalized"
    if s in {"processing", "in_progress", "queued", "pending"}:
        return "pending"
    if s in {"fail", "failed", "error"}:
        return "failed"
    return "unknown"

def compose_stamp_summary(fields: Dict[str, Optional[str]]) -> str:
    """
    Fields we expect:
      - status: normalized ("finalized" | "pending" | "failed" | "unknown")
      - uid: Optional hex id
      - proof_url: Optional URL
    """
    status = fields.get("status") or "unknown"
    uid = fields.get("uid")
    proof_url = fields.get("proof_url")
    # Friendly phrasing (matches your verify tone)
    if status == "finalized" and proof_url:
        return f"Stamp complete – proof uploaded" + (f" · UID: {uid}" if uid else "")
    # Generic fallback
    parts = [f"Status: {status}"]
    if uid:
        parts.append(f"· UID: {uid}")
    if proof_url:
        parts.append("· Proof file ready")
    return " ".join(parts)

def compose_verify_summary(fields: Dict[str, Optional[str | int]]) -> str:
    """
    Fields we expect:
      - result: e.g. "full match", "mismatch", "not_found", "error", "unknown"
      - block_number, txpow_id, transactionid
    """
    r = fields.get("result") or "unknown"
    block_number = fields.get("block_number")
    txpow_id = fields.get("txpow_id")
    transactionid = fields.get("transactionid")
    parts: list[str] = [f"Verification: {r}"]
    if block_number is not None:
        parts.append(f"· block {block_number}")
    # if txpow_id:
    #     parts.append(f"· txpow {txpow_id}")
    # if transactionid:
    #     parts.append(f"· tx {transactionid}")
    return " ".join(parts)
