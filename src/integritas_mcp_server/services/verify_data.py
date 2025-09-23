# src/integritas_mcp_server/services/verify_data.py
from __future__ import annotations

from typing import Optional
import asyncio
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

log = get_logger().bind(component="verify")


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
                return VerifyDataResponse(
                    requestId=request_id or "unknown",
                    result="error",
                    summary="Verification failed due to a local/transport issue.",
                )

            form, cleanup = normalize_form_result(built)
            if not isinstance(form, aiohttp.FormData):
                log.warning(
                    "verify_local_form_invalid",
                    req_id=request_id or "unknown",
                    form_type=str(type(form)),
                )
                return VerifyDataResponse(
                    requestId=request_id or "unknown",
                    result="error",
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
                return VerifyDataResponse(
                    requestId=request_id or "unknown",
                    result="error",
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
                return VerifyDataResponse(
                    requestId=reqid,
                    result="error",
                    block_number=None,
                    txpow_id=None,
                    transactionid=None,
                    matched_hash=None,
                    nfttxnid=None,
                    verification_url=(data.get("file") or {}).get("download_url"),
                    summary=human,
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

            return VerifyDataResponse(
                requestId=reqid,
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
            return VerifyDataResponse(
                requestId=request_id or "unknown",
                result="error",
                summary="Verification failed due to a local/transport issue.",
            )
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    log.warning("verify_cleanup_failed", req_id=request_id or "unknown")
