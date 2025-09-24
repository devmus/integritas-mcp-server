# src/integritas_mcp_server/services/verify_data.py
from __future__ import annotations
from typing import Optional, Any, Dict
from urllib.parse import urlsplit

import aiohttp

from ..models import VerifyDataRequest, VerifyDataResponse
from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart
from .tool_helpers.upload import (
    form_from_file_path,
    form_from_file_url,
    maybe_await,
    normalize_form_result,
)
from ..logging_setup import get_logger
from .envelopes import build_verify_envelope
from ._shared_summary import compose_verify_summary  # <— use the shared composer

log = get_logger().bind(component="verify")


# ----- payload extraction ------------------------------------------------------

def _extract_fields(payload: Dict[str, Any]) -> Dict[str, Optional[str | int]]:
    """
    Liberal extraction across possible upstream shapes.

    Expected sources:
      payload.status, payload.statusCode, payload.message
      payload.data.verification.data.result
      payload.data.verification.data.blockchain_data[0] -> { block_number, txpow_id, transactionid, matched_hash }
      payload.data.verification.nfttxnid
      payload.data.file.download_url
    """
    p = payload or {}
    d = p.get("data") or {}
    verification = d.get("verification") or {}
    vdata = verification.get("data") or {}
    chain_list = vdata.get("blockchain_data") or []
    chain_item = chain_list[0] if isinstance(chain_list, list) and chain_list else {}

    result = vdata.get("result") or p.get("result")
    block_number = chain_item.get("block_number")
    txpow_id = chain_item.get("txpow_id")
    transactionid = chain_item.get("transactionid")
    matched_hash = chain_item.get("matched_hash")
    uid = verification.get("nfttxnid") or p.get("uid")

    # Prefer the report's download URL
    file_obj = d.get("file") or {}
    verification_url = file_obj.get("download_url")

    # Let upstream text populate if they sent something friendly; otherwise we’ll compose
    summary = p.get("summary") or p.get("message")

    return {
        "result": result,
        "block_number": block_number,
        "txpow_id": txpow_id,
        "transactionid": transactionid,
        "matched_hash": matched_hash,
        "uid": uid,
        "verification_url": verification_url,
        "summary": summary,
    }


# ----- response factories ------------------------------------------------------

def _ok_response(
    *,
    request_id: str,
    fields: Dict[str, Optional[str | int]],
    raw: Optional[Dict[str, Any]] = None,
    summary_override: Optional[str] = None,
) -> VerifyDataResponse:
    """
    Build the standard tool response using our envelope helper.
    If summary_override is provided (e.g., upstream/human text),
    we use it; otherwise we compose a rich summary from fields.
    """
    summary = summary_override or compose_verify_summary(
        {
            "result": fields.get("result"),
            "block_number": fields.get("block_number"),
            "txpow_id": fields.get("txpow_id"),
            "transactionid": fields.get("transactionid"),
        }
    )

    pkg = build_verify_envelope(
        result=fields.get("result"),
        block_number=fields.get("block_number"),
        txpow_id=fields.get("txpow_id"),
        transactionid=fields.get("transactionid"),
        matched_hash=fields.get("matched_hash"),
        uid=fields.get("uid"),
        verification_url=fields.get("verification_url"),
        summary=summary,
        raw=raw,
    )
    return VerifyDataResponse(
        requestId=request_id,
        summary=pkg["summary"],
        structuredContent=pkg["structuredContent"],
    )


def _fail_response(
    *,
    request_id: str,
    human: str,
    maybe_verification_url: Optional[str] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> VerifyDataResponse:
    """
    Failure path: preserve the human message (no recomposition).
    """
    fields: Dict[str, Optional[str | int]] = {
        "result": "error",
        "block_number": None,
        "txpow_id": None,
        "transactionid": None,
        "matched_hash": None,
        "uid": None,
        "verification_url": maybe_verification_url,
        "summary": human,
    }
    return _ok_response(request_id=request_id, fields=fields, raw=raw, summary_override=human)


# ----- main entrypoint ---------------------------------------------------------

async def verify_data_complete(
    req: VerifyDataRequest,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> VerifyDataResponse:
    """
    Verify a proof file (JSON). Minimal error surface:
      - Upstream error envelope -> pass a friendly message through.
      - Local/transport/parsing problems -> one generic error message.

    Returns only: { requestId, summary, structuredContent }.
    """
    rid = request_id or "unknown"

    headers = build_headers(req.api_key, api_key)
    headers["x-report-required"] = "true"
    headers["x-return-format"] = "link"
    endpoint = f"{API_BASE_URL}/v1/verify/post-lite-pdf"

    # Coerce HttpUrl → str for the uploader
    file_url_str: Optional[str] = None
    if getattr(req, "file_url", None) is not None:
        try:
            file_url_str = str(req.file_url)
        except Exception:
            file_url_str = f"{req.file_url}"

    log.info(
        "verify_start",
        req_id=rid,
        has_file_url=bool(file_url_str),
        has_file_path=bool(req.file_path),
        endpoint=endpoint,
        header_keys=list(headers.keys()),
    )

    async with aiohttp.ClientSession() as session:
        cleanup = None
        try:
            # ---- Build multipart form -----------------------------------------
            try:
                built = (
                    await maybe_await(
                        form_from_file_url(session, file_url_str, "application/json")
                    )
                    if file_url_str
                    else await maybe_await(
                        form_from_file_path(req.file_path, "application/json")
                    )
                )
            except Exception as e:
                host = urlsplit(file_url_str).netloc if file_url_str else None
                log.warning("verify_local_prepare_failed", req_id=rid, host=host, err=str(e))
                return _fail_response(
                    request_id=rid,
                    human="Verification failed due to a local/transport issue.",
                )

            form, cleanup = normalize_form_result(built)
            if not isinstance(form, aiohttp.FormData):
                log.warning("verify_local_form_invalid", req_id=rid, form_type=str(type(form)))
                return _fail_response(
                    request_id=rid,
                    human="Verification failed due to a local/transport issue.",
                )

            # ---- Call upstream -------------------------------------------------
            payload = await post_multipart(session, endpoint, form, headers)

            # If HTTP helper returned raw string, treat as local/transport issue
            if isinstance(payload, str):
                log.warning("verify_local_nonjson_upstream", req_id=rid, sample=payload[:200])
                return _fail_response(
                    request_id=rid,
                    human="Verification failed due to a local/transport issue.",
                )

            # Upstream error quick check
            status = (payload.get("status") or "").lower()
            status_code = payload.get("statusCode")
            message = payload.get("message")
            data = payload.get("data") or {}
            verification = data.get("verification") or {}
            vdata = verification.get("data") or {}

            is_upstream_error = (
                status in {"error", "fail", "failed"}
                or (isinstance(status_code, int) and status_code >= 400)
                or not vdata
            )
            if is_upstream_error:
                parts = []
                if isinstance(status_code, int): parts.append(str(status_code))
                if message: parts.append(message)
                human = " | ".join(p for p in parts if p) or "Upstream verification error"
                log.info("verify_upstream_error", req_id=rid, status=status, status_code=status_code, message=message)
                return _fail_response(
                    request_id=payload.get("requestId") or rid,
                    human=human,
                    maybe_verification_url=(data.get("file") or {}).get("download_url"),
                    raw=payload,
                )

            # Success path: extract fields & envelope
            reqid = payload.get("requestId") or rid
            fields = _extract_fields(payload)

            # If upstream didn't provide a human summary, compose one
            if not fields.get("summary"):
                fields["summary"] = compose_verify_summary(
                    {
                        "result": fields.get("result"),
                        "block_number": fields.get("block_number"),
                        "txpow_id": fields.get("txpow_id"),
                        "transactionid": fields.get("transactionid"),
                    }
                )

            log.info(
                "verify_success",
                req_id=reqid,
                result=fields.get("result"),
                block_number=fields.get("block_number"),
                has_link=bool(fields.get("verification_url")),
            )

            return _ok_response(request_id=reqid, fields=fields, raw=payload)

        except Exception as e:
            log.exception("verify_local_uncaught", req_id=rid, endpoint=endpoint, err=str(e))
            return _fail_response(
                request_id=rid,
                human="Verification failed due to a local/transport issue.",
            )
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    log.warning("verify_cleanup_failed", req_id=rid)
