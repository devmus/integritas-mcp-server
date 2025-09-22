# src/integritas_mcp_server/services/verify_data.py
from __future__ import annotations


from typing import Optional
import aiohttp

from ..models import VerifyDataRequest, VerifyDataResponse
from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart
from .tool_helpers.upload import form_from_file_path, form_from_file_url, maybe_await, normalize_form_result
from ..logging_setup import get_logger

log = get_logger().bind(component="verify")



async def verify_data_complete(
    req: VerifyDataRequest,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> VerifyDataResponse:

    headers = build_headers(req.api_key, api_key)
    headers["x-report-required"] = "true"
    headers["x-return-format"] = "link"
    endpoint = f"{API_BASE_URL}/v1/verify/post-lite-pdf"

    log.info(
        "verify_start",
        req_id=request_id or "unknown",
        has_file_url=bool(req.file_url),
        has_file_path=bool(req.file_path),
        endpoint=endpoint,
        header_keys=list(headers.keys()),  # values are not logged
    )

    async with aiohttp.ClientSession() as session:
        cleanup = None
        try:
            built = (
                await maybe_await(form_from_file_url(session, req.file_url, "application/json"))
                if req.file_url
                else await maybe_await(form_from_file_path(req.file_path, "application/json"))
            )
            form, cleanup = normalize_form_result(built)
            if not isinstance(form, aiohttp.FormData):
                return VerifyDataResponse(
                    requestId=request_id or "unknown",
                    result="error",
                    summary=f"Internal error: expected FormData, got {type(form).__name__}",
                )

            payload = await post_multipart(session, endpoint, form, headers)

            # 1) Non-JSON / transport failure handled already
            if isinstance(payload, str):
                return VerifyDataResponse(
                    requestId=request_id or "unknown",
                    result="error",
                    summary=f"Upstream response not JSON: {payload[:200]}",
                )
            
            # 2) Pull common envelope bits
            reqid = payload.get("requestId") or request_id or "unknown"
            status = (payload.get("status") or "").lower()
            status_code = payload.get("statusCode")
            message = payload.get("message")
            errors_list = payload.get("errors") or []
            data = (payload or {}).get("data") or {}
            verification = data.get("verification") or {}
            file_info = data.get("file") or {}
            v_data = (verification.get("data") or {})

            # 3) If upstream reports error (or no verification section), surface it clearly
            is_upstream_error = (
                status in {"error", "fail", "failed"}
                or (isinstance(status_code, int) and status_code >= 400)
                or not v_data  # no verification payload -> something went wrong
            )

            if is_upstream_error:
                # Build a compact human summary
                parts = []
                if isinstance(status_code, int):
                    parts.append(f"{status_code}")
                if message:
                    parts.append(message)
                if errors_list:
                    parts.append("; ".join(str(e) for e in errors_list[:3]))
                if data.get("endpoint"):
                    parts.append(f"endpoint: {data['endpoint']}")
                human = " | ".join(parts) if parts else "Upstream verification error"

                return VerifyDataResponse(
                    requestId=reqid,
                    result="error",
                    block_number=None,
                    txpow_id=None,
                    transactionid=None,
                    matched_hash=None,
                    nfttxnid=None,
                    verification_url=file_info.get("download_url"),  # usually absent on error
                    summary=human,
                )

            # 4) Happy path (existing logic)
            chain_list = v_data.get("blockchain_data") or []
            chain_item = chain_list[0] if isinstance(chain_list, list) and chain_list else {}
            result = v_data.get("result") or "unknown"
            block_number = chain_item.get("block_number")
            txpow_id = chain_item.get("txpow_id")
            transactionid = chain_item.get("transactionid")
            matched_hash = chain_item.get("matched_hash")
            nfttxnid = verification.get("nfttxnid")
            verification_url = file_info.get("download_url")

            summary = (
                f"Verification: {result}"
                + (f" · block {block_number}" if block_number is not None else "")
                + (f" · txpow {txpow_id}" if txpow_id else "")
                + (f" · tx {transactionid}" if transactionid else "")
            )

            log.info(
                "verify_success",
                req_id=request_id or payload.get("requestId") or "unknown",
                result=result,
                block_number=block_number,
                has_link=bool(verification_url),
            )

            return VerifyDataResponse(
                requestId=request_id or payload.get("requestId") or "unknown",
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
            # structlog keeps full traceback with log.exception
            log.exception(
                "verify_exception",
                req_id=request_id or "unknown",
                endpoint=endpoint,
                err=str(e),
            )
            return VerifyDataResponse(
                requestId=request_id or "unknown",
                result="error",
                summary=f"Verification error: {e}",
            )
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    log.warning("verify_cleanup_failed", req_id=request_id or "unknown")
