# services/stamp_data.py
from typing import Optional
from ..models import StampDataRequest, StampDataResponse
from .tool_helpers.api import API_BASE_URL, build_headers, post_multipart, post_json, normalize_hash
from .tool_helpers.upload import form_from_file_path, form_from_file_url, maybe_await, normalize_form_result
from .stamp_data_helpers.mapping import map_payload_to_response
import aiohttp

async def stamp_data_complete(
    req: StampDataRequest,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> StampDataResponse:
    """
    If file_hash is provided, send JSON.
    Else prefer URL upload; otherwise use local file path (multipart).
    Returns a validated StampDataResponse.
    """
    if not (req.file_url or req.file_path or req.file_hash):
        return StampDataResponse(
            requestId=request_id or "unknown",
            status="failed",
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
                    return StampDataResponse(
                        requestId=request_id or "unknown",
                        status="failed",
                        summary=resp,
                    )
                return map_payload_to_response(resp, fallback_request_id=request_id)

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
                return StampDataResponse(
                    requestId=request_id or "unknown",
                    status="failed",
                    summary=resp,
                )
            return map_payload_to_response(resp, fallback_request_id=request_id)

        except Exception as e:
            return StampDataResponse(
                requestId=request_id or "unknown",
                status="failed",
                summary=f"Exception calling API: {e}",
            )
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    pass
