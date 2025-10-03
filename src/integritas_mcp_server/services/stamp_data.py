# src/integritas_mcp_server/services/stamp_data.py
from __future__ import annotations
from typing import Optional, Any, Dict

import aiohttp

from ..models import StampDataRequest, StampDataResponse
from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart, post_json
from .tool_helpers.upload import (
    form_from_file_path,
    form_from_file_url,
    maybe_await,
    normalize_form_result,
)
from ..utils.hash import normalize_hash
from ..utils.time import utc_iso
from .envelopes import build_stamp_envelope
from ._shared_summary import normalize_status, compose_stamp_summary


# ---- payload extraction -------------------------------------------------------

def _extract_fields(resp: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Be liberal in what we accept. Support both flat and nested shapes.
    We do NOT lift upstream 'message' into our summary; we compose our own.
    """
    data = resp or {}
    status_raw = (data.get("status") or data.get("state") or "").lower()
    uid = data.get("uid") or (data.get("data") or {}).get("uid")
    stamped_at = data.get("stamped_at") or (data.get("data") or {}).get("stamped_at")

    # Prefer top-level proof_url; else nested raw.data.proofFile.download_url
    proof_url = (((data.get("data") or {}).get("proofFile") or {}).get("download_url"))

    # Normalize stamped_at if it's a datetime
    try:
        from datetime import datetime as _dt
        if isinstance(stamped_at, _dt):
            stamped_at = utc_iso(stamped_at)
    except Exception:
        pass

    return {
        "status": normalize_status(status_raw),  # normalized ("finalized"|"pending"|"failed"|"unknown")
        "uid": uid,
        "stamped_at": stamped_at,
        "proof_url": proof_url,
        "summary": None,  # force our own composer
    }


# ---- response factories -------------------------------------------------------

def _ok_response(
    *,
    request_id: str,
    fields: Dict[str, Optional[str]],
    raw: Optional[Dict[str, Any]] = None,
    summary_override: Optional[str] = None,
) -> StampDataResponse:
    """
    Build the standard tool response using our envelope helper.
    If summary_override is provided (e.g., upstream/human failure text),
    we use it; otherwise we compose a rich summary from fields.
    """
    summary = summary_override or compose_stamp_summary(
        {
            "status": fields.get("status"),
            "uid": fields.get("uid"),
            "proof_url": fields.get("proof_url"),
        }
    )

    pkg = build_stamp_envelope(
        status=fields.get("status"),
        uid=fields.get("uid"),
        stamped_at=fields.get("stamped_at"),
        proof_url=fields.get("proof_url"),
        summary=summary,
        raw=raw,
    )
    return StampDataResponse(
        requestId=request_id,
        summary=pkg["summary"],
        structuredContent=pkg["structuredContent"],
    )


def _fail_response(
    *,
    request_id: str,
    human: str,
    maybe_proof_url: Optional[str] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> StampDataResponse:
    """
    Failure path: keep the human message intact (do not overwrite with a generic composer).
    """
    fields = {
        "status": "failed",
        "uid": None,
        "stamped_at": None,
        "proof_url": maybe_proof_url,
        "summary": human,
    }
    return _ok_response(request_id=request_id, fields=fields, raw=raw, summary_override=human)

def _require_api_key_or_fail(headers: Dict[str, str], rid: str):
    if "x-api-key" not in headers or not headers["x-api-key"]:
        # Single friendly surface; keep it consistent across tools
        return _fail_response(
            request_id=rid,
            human="No API key configured. Run `auth_set_api_key` once, "
                "or set INTEGRITAS_API_KEY, then retry."
        )

# ---- main entrypoint ----------------------------------------------------------

async def stamp_data_complete(
    req: StampDataRequest,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> StampDataResponse:
    """
    If file_hash is provided, send JSON; else upload file (URL preferred).
    Returns { requestId, summary, structuredContent } only.
    """
    rid = request_id or "unknown"

    headers = build_headers(req.api_key, api_key)
    maybe_err = _require_api_key_or_fail(headers, rid)
    if maybe_err:
        return maybe_err
    
    endpoint = f"{API_BASE_URL}/v1/timestamp/one-shot"

    async with aiohttp.ClientSession() as session:
        cleanup = None
        try:
            # --- HASH PATH (JSON) ------------------------------------------------
            if req.file_hash:
                h = normalize_hash(str(req.file_hash))
                resp = await post_json(session, endpoint, {"hash": h}, headers)
                if isinstance(resp, str):
                    return _fail_response(request_id=rid, human=resp)

                reqid = resp.get("requestId") or rid
                fields = _extract_fields(resp)

                if fields["status"] == "failed":
                    return _fail_response(
                        request_id=reqid,
                        human="Stamp failed.",
                        maybe_proof_url=fields.get("proof_url"),
                        raw=resp,
                    )

                return _ok_response(request_id=reqid, fields=fields, raw=resp)

            # --- MULTIPART PATH (URL or local file) -----------------------------
            if req.file_url:
                built = await maybe_await(
                    form_from_file_url(session, str(req.file_url), "application/octet-stream")
                )
            else:
                built = await maybe_await(
                    form_from_file_path(req.file_path, "application/octet-stream")
                )

            form, cleanup = normalize_form_result(built)
            resp = await post_multipart(session, endpoint, form, headers)
            if isinstance(resp, str):
                return _fail_response(request_id=rid, human=resp)

            reqid = resp.get("requestId") or rid
            fields = _extract_fields(resp)

            if fields["status"] == "failed":
                return _fail_response(
                    request_id=reqid,
                    human="Stamp failed.",
                    maybe_proof_url=fields.get("proof_url"),
                    raw=resp,
                )

            return _ok_response(request_id=reqid, fields=fields, raw=resp)

        except Exception as e:
            # Keep a single friendly error surface
            return _fail_response(request_id=rid, human=f"Exception calling API: {e}")

        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    pass
