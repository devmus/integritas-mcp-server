# # # src/integritas_mcp_server/services/verify_data.py
# # from __future__ import annotations


# # from typing import Optional
# # import aiohttp

# # from ..models import VerifyDataRequest, VerifyDataResponse
# # from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart
# # from .tool_helpers.upload import form_from_file_path, form_from_file_url, maybe_await, normalize_form_result
# # from ..logging_setup import get_logger

# # log = get_logger().bind(component="verify")



# # async def verify_data_complete(
# #     req: VerifyDataRequest,
# #     request_id: Optional[str] = None,
# #     api_key: Optional[str] = None,
# # ) -> VerifyDataResponse:

# #     headers = build_headers(req.api_key, api_key)
# #     headers["x-report-required"] = "true"
# #     headers["x-return-format"] = "link"
# #     endpoint = f"{API_BASE_URL}/v1/verify/post-lite-pdf"

# #     log.info(
# #         "verify_start",
# #         req_id=request_id or "unknown",
# #         has_file_url=bool(req.file_url),
# #         has_file_path=bool(req.file_path),
# #         endpoint=endpoint,
# #         header_keys=list(headers.keys()),  # values are not logged
# #     )

# #     async with aiohttp.ClientSession() as session:
# #         cleanup = None
# #         try:
# #             built = (
# #                 await maybe_await(form_from_file_url(session, req.file_url, "application/json"))
# #                 if req.file_url
# #                 else await maybe_await(form_from_file_path(req.file_path, "application/json"))
# #             )
# #             form, cleanup = normalize_form_result(built)
# #             if not isinstance(form, aiohttp.FormData):
# #                 return VerifyDataResponse(
# #                     requestId=request_id or "unknown",
# #                     result="error",
# #                     summary=f"Internal error: expected FormData, got {type(form).__name__}",
# #                 )

# #             payload = await post_multipart(session, endpoint, form, headers)

# #             # 1) Non-JSON / transport failure handled already
# #             if isinstance(payload, str):
# #                 return VerifyDataResponse(
# #                     requestId=request_id or "unknown",
# #                     result="error",
# #                     summary=f"Upstream response not JSON: {payload[:200]}",
# #                 )
            
# #             # 2) Pull common envelope bits
# #             reqid = payload.get("requestId") or request_id or "unknown"
# #             status = (payload.get("status") or "").lower()
# #             status_code = payload.get("statusCode")
# #             message = payload.get("message")
# #             errors_list = payload.get("errors") or []
# #             data = (payload or {}).get("data") or {}
# #             verification = data.get("verification") or {}
# #             file_info = data.get("file") or {}
# #             v_data = (verification.get("data") or {})

# #             # 3) If upstream reports error (or no verification section), surface it clearly
# #             is_upstream_error = (
# #                 status in {"error", "fail", "failed"}
# #                 or (isinstance(status_code, int) and status_code >= 400)
# #                 or not v_data  # no verification payload -> something went wrong
# #             )

# #             if is_upstream_error:
# #                 # Build a compact human summary
# #                 parts = []
# #                 if isinstance(status_code, int):
# #                     parts.append(f"{status_code}")
# #                 if message:
# #                     parts.append(message)
# #                 if errors_list:
# #                     parts.append("; ".join(str(e) for e in errors_list[:3]))
# #                 if data.get("endpoint"):
# #                     parts.append(f"endpoint: {data['endpoint']}")
# #                 human = " | ".join(parts) if parts else "Upstream verification error"

# #                 return VerifyDataResponse(
# #                     requestId=reqid,
# #                     result="error",
# #                     block_number=None,
# #                     txpow_id=None,
# #                     transactionid=None,
# #                     matched_hash=None,
# #                     nfttxnid=None,
# #                     verification_url=file_info.get("download_url"),  # usually absent on error
# #                     summary=human,
# #                 )

# #             # 4) Happy path (existing logic)
# #             chain_list = v_data.get("blockchain_data") or []
# #             chain_item = chain_list[0] if isinstance(chain_list, list) and chain_list else {}
# #             result = v_data.get("result") or "unknown"
# #             block_number = chain_item.get("block_number")
# #             txpow_id = chain_item.get("txpow_id")
# #             transactionid = chain_item.get("transactionid")
# #             matched_hash = chain_item.get("matched_hash")
# #             nfttxnid = verification.get("nfttxnid")
# #             verification_url = file_info.get("download_url")

# #             summary = (
# #                 f"Verification: {result}"
# #                 + (f" · block {block_number}" if block_number is not None else "")
# #                 + (f" · txpow {txpow_id}" if txpow_id else "")
# #                 + (f" · tx {transactionid}" if transactionid else "")
# #             )

# #             log.info(
# #                 "verify_success",
# #                 req_id=request_id or payload.get("requestId") or "unknown",
# #                 result=result,
# #                 block_number=block_number,
# #                 has_link=bool(verification_url),
# #             )

# #             return VerifyDataResponse(
# #                 requestId=request_id or payload.get("requestId") or "unknown",
# #                 result=result,
# #                 block_number=block_number,
# #                 txpow_id=txpow_id,
# #                 transactionid=transactionid,
# #                 matched_hash=matched_hash,
# #                 nfttxnid=nfttxnid,
# #                 verification_url=verification_url,
# #                 summary=summary,
# #             )

# #         except Exception as e:
# #             # structlog keeps full traceback with log.exception
# #             log.exception(
# #                 "verify_exception",
# #                 req_id=request_id or "unknown",
# #                 endpoint=endpoint,
# #                 err=str(e),
# #             )
# #             return VerifyDataResponse(
# #                 requestId=request_id or "unknown",
# #                 result="error",
# #                 summary=f"Verification error: {e}",
# #             )
# #         finally:
# #             if cleanup:
# #                 try:
# #                     cleanup()
# #                 except Exception:
# #                     log.warning("verify_cleanup_failed", req_id=request_id or "unknown")

# # src/integritas_mcp_server/services/verify_data.py
# from __future__ import annotations

# from typing import Optional
# import asyncio
# from urllib.parse import urlsplit

# import aiohttp
# from aiohttp import ClientConnectorError, ClientResponseError

# from ..models import VerifyDataRequest, VerifyDataResponse
# from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart
# from .tool_helpers.upload import (
#     form_from_file_path,
#     form_from_file_url,
#     maybe_await,
#     normalize_form_result,
# )
# from ..logging_setup import get_logger

# log = get_logger().bind(component="verify")


# async def verify_data_complete(
#     req: VerifyDataRequest,
#     request_id: Optional[str] = None,
#     api_key: Optional[str] = None,
# ) -> VerifyDataResponse:
#     """
#     Verifies a proof JSON (by URL or path) via the upstream /v1/verify/post-lite-pdf endpoint.
#     Returns clearer, user-friendly error summaries for:
#       - Proof URL 404 / unreachable / timeout
#       - Bad JSON (non-JSON proof)
#       - Upstream chain not found
#       - Unexpected upstream statuses
#     """

#     headers = build_headers(req.api_key, api_key)
#     headers["x-report-required"] = "true"
#     headers["x-return-format"] = "link"
#     endpoint = f"{API_BASE_URL}/v1/verify/post-lite-pdf"

#     log.info(
#         "verify_start",
#         req_id=request_id or "unknown",
#         has_file_url=bool(req.file_url),
#         has_file_path=bool(req.file_path),
#         endpoint=endpoint,
#         header_keys=list(headers.keys()),  # values are not logged
#     )

#     async with aiohttp.ClientSession() as session:
#         cleanup = None
#         try:
#             # ---------- (A) Build the multipart form, with precise error mapping ----------
#             try:
#                 built = (
#                     await maybe_await(
#                         form_from_file_url(session, req.file_url, "application/json")
#                     )
#                     if req.file_url
#                     else await maybe_await(
#                         form_from_file_path(req.file_path, "application/json")
#                     )
#                 )
#             except ClientResponseError as e:
#                 # Errors while fetching the proof URL
#                 host = urlsplit(req.file_url or "").netloc if req.file_url else None
#                 if e.status == 404:
#                     msg = f"Proof file not found (HTTP 404){f' at {host}' if host else ''}."
#                 else:
#                     msg = f"Unexpected HTTP status {e.status} while fetching proof file."
#                 log.warning(
#                     "verify_fetch_proof_http_error",
#                     req_id=request_id or "unknown",
#                     status=e.status,
#                     host=host,
#                 )
#                 return VerifyDataResponse(
#                     requestId=request_id or "unknown",
#                     result="error",
#                     summary=msg,
#                 )
#             except ClientConnectorError as e:
#                 host = urlsplit(req.file_url or "").netloc if req.file_url else None
#                 log.warning(
#                     "verify_fetch_proof_host_unreachable",
#                     req_id=request_id or "unknown",
#                     host=host,
#                     err=str(e),
#                 )
#                 return VerifyDataResponse(
#                     requestId=request_id or "unknown",
#                     result="error",
#                     summary=f"Proof URL host unreachable{f' ({host})' if host else ''}.",
#                 )
#             except asyncio.TimeoutError:
#                 log.warning(
#                     "verify_fetch_proof_timeout",
#                     req_id=request_id or "unknown",
#                 )
#                 return VerifyDataResponse(
#                     requestId=request_id or "unknown",
#                     result="error",
#                     summary="Timed out downloading proof file.",
#                 )
#             except ValueError as e:
#                 # e.g., if helper tried to parse/validate JSON and failed
#                 log.warning(
#                     "verify_fetch_proof_bad_json",
#                     req_id=request_id or "unknown",
#                     err=str(e),
#                 )
#                 return VerifyDataResponse(
#                     requestId=request_id or "unknown",
#                     result="error",
#                     summary=f"Downloaded proof is not valid JSON: {e}",
#                 )
#             except Exception as e:
#                 log.warning(
#                     "verify_fetch_proof_unknown_error",
#                     req_id=request_id or "unknown",
#                     err=str(e),
#                 )
#                 return VerifyDataResponse(
#                     requestId=request_id or "unknown",
#                     result="error",
#                     summary=f"Unexpected error fetching proof file: {e}",
#                 )

#             # Normalize the form result from helper
#             form, cleanup = normalize_form_result(built)
#             if not isinstance(form, aiohttp.FormData):
#                 return VerifyDataResponse(
#                     requestId=request_id or "unknown",
#                     result="error",
#                     summary=f"Internal error: expected FormData, got {type(form).__name__}",
#                 )

#             # ---------- (B) Call upstream, keep transport & JSON parsing distinct ----------
#             payload = await post_multipart(session, endpoint, form, headers)

#             # Non-JSON / raw error string already handled inside post_multipart
#             if isinstance(payload, str):
#                 # Be explicit that the upstream didn't return JSON
#                 return VerifyDataResponse(
#                     requestId=request_id or "unknown",
#                     result="error",
#                     summary=f"Upstream response not JSON: {payload[:200]}",
#                 )

#             # ---------- (C) Pull common envelope bits ----------
#             reqid = payload.get("requestId") or request_id or "unknown"
#             status = (payload.get("status") or "").lower()
#             status_code = payload.get("statusCode")
#             message = payload.get("message")
#             errors_list = payload.get("errors") or []
#             data = (payload or {}).get("data") or {}
#             verification = data.get("verification") or {}
#             file_info = data.get("file") or {}
#             v_data = (verification.get("data") or {})

#             # ---------- (D) Clear upstream error mapping ----------
#             is_upstream_error = (
#                 status in {"error", "fail", "failed"}
#                 or (isinstance(status_code, int) and status_code >= 400)
#                 or not v_data  # no verification payload -> something went wrong
#             )

#             if is_upstream_error:
#                 # Try to identify common failure modes for human-friendly text
#                 human_parts = []

#                 if isinstance(status_code, int):
#                     human_parts.append(str(status_code))
#                 if message:
#                     human_parts.append(message)

#                 if errors_list:
#                     human_parts.append("; ".join(str(e) for e in errors_list[:3]))

#                 # Heuristics for "hash not found on-chain"
#                 # (Adjust these keys/strings to match your upstream payloads)
#                 reason = (v_data.get("reason") or "").lower()
#                 if (
#                     "not found" in (message or "").lower()
#                     or "not found" in reason
#                     or (status_code == 404)
#                 ):
#                     human_parts.append("Hash not found on-chain for the provided proof")

#                 if data.get("endpoint"):
#                     human_parts.append(f"endpoint: {data['endpoint']}")

#                 human = " | ".join(p for p in human_parts if p) or "Upstream verification error"

#                 return VerifyDataResponse(
#                     requestId=reqid,
#                     result="error",
#                     block_number=None,
#                     txpow_id=None,
#                     transactionid=None,
#                     matched_hash=None,
#                     nfttxnid=None,
#                     verification_url=file_info.get("download_url"),  # may be absent on error
#                     summary=human,
#                 )

#             # ---------- (E) Happy path ----------
#             chain_list = v_data.get("blockchain_data") or []
#             chain_item = chain_list[0] if isinstance(chain_list, list) and chain_list else {}
#             result = v_data.get("result") or "unknown"
#             block_number = chain_item.get("block_number")
#             txpow_id = chain_item.get("txpow_id")
#             transactionid = chain_item.get("transactionid")
#             matched_hash = chain_item.get("matched_hash")
#             nfttxnid = verification.get("nfttxnid")
#             verification_url = file_info.get("download_url")

#             summary = (
#                 f"Verification: {result}"
#                 + (f" · block {block_number}" if block_number is not None else "")
#                 + (f" · txpow {txpow_id}" if txpow_id else "")
#                 + (f" · tx {transactionid}" if transactionid else "")
#             )

#             log.info(
#                 "verify_success",
#                 req_id=request_id or payload.get("requestId") or "unknown",
#                 result=result,
#                 block_number=block_number,
#                 has_link=bool(verification_url),
#             )

#             return VerifyDataResponse(
#                 requestId=request_id or payload.get("requestId") or "unknown",
#                 result=result,
#                 block_number=block_number,
#                 txpow_id=txpow_id,
#                 transactionid=transactionid,
#                 matched_hash=matched_hash,
#                 nfttxnid=nfttxnid,
#                 verification_url=verification_url,
#                 summary=summary,
#             )

#         except Exception as e:
#             # structlog keeps full traceback with log.exception
#             log.exception(
#                 "verify_exception",
#                 req_id=request_id or "unknown",
#                 endpoint=endpoint,
#                 err=str(e),
#             )
#             return VerifyDataResponse(
#                 requestId=request_id or "unknown",
#                 result="error",
#                 summary=f"Verification error: {e}",
#             )
#         finally:
#             if cleanup:
#                 try:
#                     cleanup()
#                 except Exception:
#                     log.warning("verify_cleanup_failed", req_id=request_id or "unknown")


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
