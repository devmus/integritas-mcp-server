# services/stamp_data.py
from typing import Optional, Any, Dict
from datetime import datetime, timezone
import aiohttp

from ..models import StampDataRequest, StampDataResponse,ToolResultEnvelopeV1,ToolLink

from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart, post_json, normalize_hash
from .tool_helpers.upload import (form_from_file_path, form_from_file_url, maybe_await, normalize_form_result)
# from .stamp_data_helpers.mapping import map_payload_to_response

# ---- small utils ----

def utc_iso(dt: Optional[datetime] = None) -> str:
    """ISO-8601 in UTC with Z suffix."""
    return (dt or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")


def stamp_to_envelope(
    *,
    status: str,                       # "pending" | "finalized" | "failed" | unknown
    uid: Optional[str],
    stamped_at: Optional[str],
    proof_url: Optional[str],
    summary: str,
    raw: Optional[Dict[str, Any]] = None,
) -> dict:
    env = ToolResultEnvelopeV1(
        kind="integritas/stamp_result@v1",
        status=(status or "unknown"),
        summary=summary,
        ids=({"uid": uid} if uid else None),
        timestamps=({"stamped_at": stamped_at} if stamped_at else None),
        links=([ToolLink(rel="proof", href=proof_url, label="Download proof")] if proof_url else None),
        data={
            "status": status,
            "uid": uid,
            "stamped_at": stamped_at,
            "proof_url": proof_url,
            "raw": raw or {},
        },
        **{"$schema": "https://integritas.dev/schemas/tool-result-v1.json"},
    )
    return {
        "summary": summary,
        "structuredContent": env.model_dump(by_alias=True, exclude_none=True),
    }


def _ok_response(
    *,
    request_id: str,
    status: str,
    uid: Optional[str],
    stamped_at: Optional[str],
    proof_url: Optional[str],
    summary: str,
    raw: Optional[Dict[str, Any]] = None,
) -> StampDataResponse:
    pkg = stamp_to_envelope(
        status=status,
        uid=uid,
        stamped_at=stamped_at,
        proof_url=proof_url,
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
    summary: str,
    proof_url: Optional[str] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> StampDataResponse:
    pkg = stamp_to_envelope(
        status="failed",
        uid=None,
        stamped_at=None,
        proof_url=proof_url,
        summary=summary,
        raw=raw,
    )
    return StampDataResponse(
        requestId=request_id,
        summary=pkg["summary"],
        structuredContent=pkg["structuredContent"],
    )


# ---- extraction helpers ----

def _extract_fields(resp: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Be liberal in what we accept. Support both flat and nested shapes.
    Expected keys in the wild:
      - status: "pending" | "finalized" | "failed"
      - uid
      - stamped_at (ISO)
      - proof_url
      - summary (optional)
    """
    data = resp or {}
    status = (data.get("status") or data.get("state") or "").lower()
    uid = data.get("uid") or (data.get("data") or {}).get("uid")
    stamped_at = data.get("stamped_at") or (data.get("data") or {}).get("stamped_at")
    proof_url = data.get("proof_url") or (data.get("data") or {}).get("proof_url")
    summary = data.get("summary")

    # Normalize stamped_at if it's a datetime
    if isinstance(stamped_at, datetime):
        stamped_at = utc_iso(stamped_at)

    return {
        "status": status or "unknown",
        "uid": uid,
        "stamped_at": stamped_at,
        "proof_url": proof_url,
        "summary": summary,
    }


# # ---- main entrypoint ----


# async def stamp_data_complete(
#     req: StampDataRequest,
#     request_id: Optional[str] = None,
#     api_key: Optional[str] = None,
# ) -> StampDataResponse:
#     """
#     If file_hash is provided, send JSON.
#     Else prefer URL upload; otherwise use local file path (multipart).
#     Returns a validated StampDataResponse.
#     """
#     if not (req.file_url or req.file_path or req.file_hash):
#         return StampDataResponse(
#             requestId=request_id or "unknown",
#             status="failed",
#             summary="Neither file_url, file_path, nor file_hash provided.",
#         )

#     headers = build_headers(req.api_key, api_key)
#     endpoint = f"{API_BASE_URL}/v1/timestamp/one-shot"

#     async with aiohttp.ClientSession() as session:
#         cleanup = None
#         try:
#             # --- HASH PATH (JSON) ---
#             if req.file_hash:
#                 h = normalize_hash(str(req.file_hash))
#                 resp = await post_json(session, endpoint, {"hash": h}, headers)
#                 if isinstance(resp, str):
#                     return StampDataResponse(
#                         requestId=request_id or "unknown",
#                         status="failed",
#                         summary=resp,
#                     )
#                 return map_payload_to_response(resp, fallback_request_id=request_id)

#             # --- MULTIPART PATH (URL or local file) ---
#             if req.file_url:
#                 built = await maybe_await(
#                     form_from_file_url(session, str(req.file_url), "application/octet-stream")
#                 )
#             else:
#                 built = await maybe_await(
#                     form_from_file_path(req.file_path, "application/octet-stream")
#                 )

#             form, cleanup = normalize_form_result(built)

#             resp = await post_multipart(session, endpoint, form, headers)
#             if isinstance(resp, str):
#                 return StampDataResponse(
#                     requestId=request_id or "unknown",
#                     status="failed",
#                     summary=resp,
#                 )
#             return map_payload_to_response(resp, fallback_request_id=request_id)

#         except Exception as e:
#             return StampDataResponse(
#                 requestId=request_id or "unknown",
#                 status="failed",
#                 summary=f"Exception calling API: {e}",
#             )
#         finally:
#             if cleanup:
#                 try:
#                     cleanup()
#                 except Exception:
#                     pass

# ---- main entrypoint ----

async def stamp_data_complete(
    req: StampDataRequest,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> StampDataResponse:
    """
    If file_hash is provided, send JSON.
    Else prefer URL upload; otherwise use local file path (multipart).
    Returns a StampDataResponse with { summary, structuredContent }.
    """
    rid = request_id or "unknown"

    if not (req.file_url or req.file_path or req.file_hash):
        return _fail_response(
            request_id=rid,
            summary="Neither file_url, file_path, nor file_hash provided.",
        )

    headers = build_headers(req.api_key, api_key)
    endpoint = f"{API_BASE_URL}/v1/timestamp/one-shot"

    async with aiohttp.ClientSession() as session:
        cleanup = None
        try:
            # --- HASH PATH (JSON) ---
            if req.file_hash:
                h = normalize_hash(str(req.file_hash))
                resp = await post_json(session, endpoint, {"hash": h}, headers)
                if isinstance(resp, str):
                    return _fail_response(request_id=rid, summary=resp)

                reqid = resp.get("requestId") or rid
                fields = _extract_fields(resp)
                status = fields["status"] or "unknown"
                uid = fields["uid"]
                stamped_at = fields["stamped_at"]
                proof_url = fields["proof_url"]

                # Prefer server-provided summary; else build one
                summary = fields["summary"] or (
                    f"Status: {status}"
                    + (f" · UID: {uid}" if uid else "")
                    + (" · Proof file ready" if proof_url else "")
                )

                if status in {"failed", "error"}:
                    return _fail_response(
                        request_id=reqid, summary=summary, proof_url=proof_url, raw=resp
                    )
                return _ok_response(
                    request_id=reqid,
                    status=status,
                    uid=uid,
                    stamped_at=stamped_at,
                    proof_url=proof_url,
                    summary=summary,
                    raw=resp,
                )

            # --- MULTIPART PATH (URL or local file) ---
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
                return _fail_response(request_id=rid, summary=resp)

            reqid = resp.get("requestId") or rid
            fields = _extract_fields(resp)
            status = fields["status"] or "unknown"
            uid = fields["uid"]
            stamped_at = fields["stamped_at"]
            proof_url = fields["proof_url"]

            summary = fields["summary"] or (
                f"Status: {status}"
                + (f" · UID: {uid}" if uid else "")
                + (" · Proof file ready" if proof_url else "")
            )

            if status in {"failed", "error"}:
                return _fail_response(
                    request_id=reqid, summary=summary, proof_url=proof_url, raw=resp
                )
            return _ok_response(
                request_id=reqid,
                status=status,
                uid=uid,
                stamped_at=stamped_at,
                proof_url=proof_url,
                summary=summary,
                raw=resp,
            )

        except Exception as e:
            # Keep a single friendly error surface
            return _fail_response(
                request_id=rid, summary=f"Exception calling API: {e}"
            )
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    pass