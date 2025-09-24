from __future__ import annotations
from typing import Optional, Any, Dict

from ..models import ToolResultEnvelopeV1, ToolLink, STAMP_RESULT_KIND, VERIFY_RESULT_KIND
from ..utils.time import utc_iso


# ----- canonical status mappers ------------------------------------------------

def canonical_status(s: Optional[str]) -> str:
    m = (s or "").lower()
    return {
        "success": "finalized",
        "ok": "finalized",
        "finalized": "finalized",
        "pending": "pending",
        "processing": "pending",
        "queued": "pending",
        "failed": "failed",
        "error": "failed",
    }.get(m, "unknown")

def canonical_verify_status(result: Optional[str]) -> str:
    m = (result or "").lower()
    return {
        # positive
        "match": "finalized",
        "ok": "finalized",
        "exists": "finalized",
        "found": "finalized",
        "success": "finalized",
        # negative/error
        "mismatch": "failed",
        "no_match": "failed",
        "not_found": "failed",
        "missing": "failed",
        "error": "failed",
        "failed": "failed",
    }.get(m, "unknown")


# ----- stamp envelope ----------------------------------------------------------

def build_stamp_envelope(
    *,
    status: Optional[str],
    uid: Optional[str],
    stamped_at: Optional[str],
    proof_url: Optional[str],
    summary: str,
    raw: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    env = ToolResultEnvelopeV1(
        kind=STAMP_RESULT_KIND,
        status=canonical_status(status),
        summary=summary,
        ids=({"uid": uid} if uid else None),
        timestamps=({"stamped_at": utc_iso(stamped_at)} if stamped_at else None),
        links=([ToolLink(rel="proof", href=proof_url, label="Download proof")] if proof_url else None),
        data={"status": status, "uid": uid, "stamped_at": stamped_at, "proof_url": proof_url, "raw": raw or {}},
    )
    return {"summary": summary, "structuredContent": env.model_dump(by_alias=True, exclude_none=True)}


# ----- verify envelope ---------------------------------------------------------

def build_verify_envelope(
    *,
    result: Optional[str],
    block_number: Optional[int],
    txpow_id: Optional[str],
    transactionid: Optional[str],
    matched_hash: Optional[str],
    uid: Optional[str],
    verification_url: Optional[str],
    summary: str,
    raw: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ids = {}
    if txpow_id: ids["txpow_id"] = txpow_id
    if transactionid: ids["tx_id"] = transactionid
    if uid: ids["uid"] = uid
    if matched_hash: ids["matched_hash"] = matched_hash

    ts = {"verified_at": utc_iso()}
    if block_number is not None:
        ts["block_number"] = str(block_number)

    env = ToolResultEnvelopeV1(
        kind=VERIFY_RESULT_KIND,
        status=canonical_verify_status(result),
        summary=summary,
        ids=(ids or None),
        timestamps=(ts or None),
        links=([ToolLink(rel="verification", href=verification_url, label="View verification")] if verification_url else None),
        data={
            "result": result,
            "block_number": block_number,
            "txpow_id": txpow_id,
            "transactionid": transactionid,
            "matched_hash": matched_hash,
            "uid": uid,
            "verification_url": verification_url,
            "raw": raw or {},
        },
    )
    return {"summary": summary, "structuredContent": env.model_dump(by_alias=True, exclude_none=True)}
