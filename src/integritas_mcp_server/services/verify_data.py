# src/integritas_mcp_server/services/verify_data.py
from __future__ import annotations
from typing import Optional
from urllib.parse import urlsplit
from datetime import datetime, timezone
import aiohttp

from ..models import VerifyDataRequest, VerifyDataResponse, ToolResultEnvelopeV1, ToolLink
from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart
from .tool_helpers.upload import (
    form_from_file_path,
    form_from_file_url,
    maybe_await,
    normalize_form_result,
)
from ..logging_setup import get_logger

log = get_logger().bind(component="verify")

# ---- small utils ----

def utc_iso(dt: Optional[datetime] = None) -> str:
    """ISO-8601 in UTC with Z suffix."""
    return (dt or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")


def verify_to_envelope(
    *,
    result: str,
    block_number: Optional[int],
    txpow_id: Optional[str],
    transactionid: Optional[str],
    matched_hash: Optional[str],
    nfttxnid: Optional[str],
    verification_url: Optional[str],
    summary: str,
) -> dict:
    status = "finalized" if result in ("match", "finalized", "ok", "exists") else \
             ("failed" if result in ("mismatch", "not_found", "error") else "unknown")

    env = ToolResultEnvelopeV1(
        kind="integritas/verify_result@v1",
        status=status,
        summary=summary,
        ids={
            **({"txpow_id": txpow_id} if txpow_id else {}),
            **({"tx_id": transactionid} if transactionid else {}),
            **({"uid": nfttxnid} if nfttxnid else {}),
            **({"matched_hash": matched_hash} if matched_hash else {}),
        } or None,
        timestamps={
            "verified_at": utc_iso(),
            **({"block_number": str(block_number)} if block_number is not None else {}),
        } or None,
        links=(
            [ToolLink(rel="verification", href=verification_url, label="View verification")]
            if verification_url else None
        ),
        data={
            "result": result,
            "block_number": block_number,
            "txpow_id": txpow_id,
            "transactionid": transactionid,
            "matched_hash": matched_hash,
            "nfttxnid": nfttxnid,
            "verification_url": verification_url,
        },
        **{"$schema": "https://integritas.dev/schemas/tool-result-v1.json"},
    )

    # MCP servers usually return { summary, structuredContent }
    return {
        "summary": summary,                           # plain text for transcript
        "structuredContent": env.model_dump(by_alias=True, exclude_none=True),
    }


def _ok_response(
    *,
    request_id: str,
    result: str,
    block_number: Optional[int],
    txpow_id: Optional[str],
    transactionid: Optional[str],
    matched_hash: Optional[str],
    nfttxnid: Optional[str],
    verification_url: Optional[str],
    summary: str,
) -> VerifyDataResponse:
    pkg = verify_to_envelope(
        result=result,
        block_number=block_number,
        txpow_id=txpow_id,
        transactionid=transactionid,
        matched_hash=matched_hash,
        nfttxnid=nfttxnid,
        verification_url=verification_url,
        summary=summary,
    )
    return VerifyDataResponse(
        requestId=request_id,
        summary=pkg["summary"],
        structuredContent=pkg["structuredContent"],
    )

def _fail_response(
    *,
    request_id: str,
    summary: str,
    verification_url: Optional[str] = None,
) -> VerifyDataResponse:
    # Minimal failed envelope (no chain ids)
    pkg = verify_to_envelope(
        result="error",
        block_number=None,
        txpow_id=None,
        transactionid=None,
        matched_hash=None,
        nfttxnid=None,
        verification_url=verification_url,
        summary=summary,
    )
    return VerifyDataResponse(
        requestId=request_id,
        summary=pkg["summary"],
        structuredContent=pkg["structuredContent"],
    )

async def verify_data_complete(
    req: VerifyDataRequest,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> VerifyDataResponse:
    """
    Very small error surface:
      - If upstream returns an error envelope -> pass that back (Upstream error).
      - Otherwise, ANY local/transport/parsing problem -> single generic error message.
    """

    headers = build_headers(req.api_key, api_key)
    headers["x-report-required"] = "true"
    headers["x-return-format"] = "link"
    endpoint = f"{API_BASE_URL}/v1/verify/post-lite-pdf"

    # Coerce HttpUrl -> str early to avoid .decode errors
    file_url_str: Optional[str] = None
    if getattr(req, "file_url", None) is not None:
        try:
            file_url_str = str(req.file_url)
        except Exception:
            file_url_str = f"{req.file_url}"

    log.info(
        "verify_start",
        req_id=request_id or "unknown",
        has_file_url=bool(file_url_str),
        has_file_path=bool(req.file_path),
        endpoint=endpoint,
        header_keys=list(headers.keys()),  # values are not logged
    )

    async with aiohttp.ClientSession() as session:
        cleanup = None
        try:
            # ---- Build multipart form (generic local error on any failure) ----
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
                log.warning(
                    "verify_local_prepare_failed",
                    req_id=request_id or "unknown",
                    host=host,
                    err=str(e),
                )

                return _fail_response(
                request_id=request_id or "unknown",
                summary="Verification failed due to a local/transport issue.",
                )

            form, cleanup = normalize_form_result(built)
            if not isinstance(form, aiohttp.FormData):
                log.warning(
                    "verify_local_form_invalid",
                    req_id=request_id or "unknown",
                    form_type=str(type(form)),
                )
                return _fail_response(
                    request_id=request_id or "unknown",
                    summary="Verification failed due to a local/transport issue.",
                )

            # ---- Call upstream (only two outcomes: success OR upstream error) ----
            payload = await post_multipart(session, endpoint, form, headers)

            # If our HTTP helper returned a raw string, treat it as local/transport issue
            if isinstance(payload, str):
                log.warning(
                    "verify_local_nonjson_upstream",
                    req_id=request_id or "unknown",
                    sample=payload[:200],
                )
                return _fail_response(
                    request_id=request_id or "unknown",
                    summary="Verification failed due to a local/transport issue.",
                )

            # Pull envelope
            reqid = payload.get("requestId") or request_id or "unknown"
            status = (payload.get("status") or "").lower()
            status_code = payload.get("statusCode")
            message = payload.get("message")
            data = (payload or {}).get("data") or {}
            verification = data.get("verification") or {}
            v_data = (verification.get("data") or {})

            # ---- Upstream error path (pass upstream message/status through) ----
            is_upstream_error = (
                status in {"error", "fail", "failed"}
                or (isinstance(status_code, int) and status_code >= 400)
                or not v_data
            )
            if is_upstream_error:
                # Compose a compact upstream message, but do not add more categories
                parts = []
                if isinstance(status_code, int):
                    parts.append(str(status_code))
                if message:
                    parts.append(message)
                human = " | ".join(p for p in parts if p) or "Upstream verification error"

                log.info(
                    "verify_upstream_error",
                    req_id=reqid,
                    status=status,
                    status_code=status_code,
                    message=message,
                )
                return _fail_response(
                    request_id=reqid,
                    summary=human,
                    verification_url=(data.get("file") or {}).get("download_url"),
                )

            # ---- Success path (unchanged) ----
            chain_list = v_data.get("blockchain_data") or []
            chain_item = chain_list[0] if isinstance(chain_list, list) and chain_list else {}
            result = v_data.get("result") or "unknown"
            block_number = chain_item.get("block_number")
            txpow_id = chain_item.get("txpow_id")
            transactionid = chain_item.get("transactionid")
            matched_hash = chain_item.get("matched_hash")
            nfttxnid = verification.get("nfttxnid")
            verification_url = (data.get("file") or {}).get("download_url")

            summary = (
                f"Verification: {result}"
                + (f" · block {block_number}" if block_number is not None else "")
                + (f" · txpow {txpow_id}" if txpow_id else "")
                + (f" · tx {transactionid}" if transactionid else "")
            )

            log.info(
                "verify_success",
                req_id=reqid,
                result=result,
                block_number=block_number,
                has_link=bool(verification_url),
            )

            return _ok_response(
                request_id=reqid,
                result=result,
                block_number=block_number,
                txpow_id=txpow_id,
                transactionid=transactionid,
                matched_hash=matched_hash,
                nfttxnid=nfttxnid,
                verification_url=verification_url,
                summary=summary,
            )

        except Exception as e:
            # Catch-all -> still the same single local/transport error for the client
            log.exception(
                "verify_local_uncaught",
                req_id=request_id or "unknown",
                endpoint=endpoint,
                err=str(e),
            )
            return _fail_response(
                request_id=request_id or "unknown",
                summary="Verification failed due to a local/transport issue.",
            )
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    log.warning("verify_cleanup_failed", req_id=request_id or "unknown")
