# services/stamp_data.py
from typing import Optional
from ..models import StampDataRequest, StampDataResponse
from .stamp_data_helpers.api import API_BASE_URL, build_headers, post_multipart
from .stamp_data_helpers.upload import form_from_file_path, form_from_file_url
from .stamp_data_helpers.mapping import map_payload_to_response

import aiohttp

async def stamp_data_complete(
    req: StampDataRequest,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> StampDataResponse:
    """
    Prefer URL upload if present; otherwise use local file path.
    Returns a validated StampDataResponse.
    """
    # quick input guard (the model should already enforce one-of)
    if not (req.file_url or req.file_path):
        return StampDataResponse(
            requestId=request_id or "unknown",
            status="failed",
            summary="Neither file_url nor file_path provided.",
        )

    headers = build_headers(req.api_key, api_key)
    endpoint = f"{API_BASE_URL}/v1/timestamp/one-shot"

    async with aiohttp.ClientSession() as session:
        try:
            if req.file_url:
                form = await form_from_file_url(session, str(req.file_url))
            else:
                ok, form_or_err = form_from_file_path(req.file_path)
                if not ok:
                    return StampDataResponse(
                        requestId=request_id or "unknown",
                        status="failed",
                        summary=form_or_err,  # error message
                    )
                form = form_or_err

            payload_or_err = await post_multipart(session, endpoint, form, headers)
            if isinstance(payload_or_err, str):
                return StampDataResponse(
                    requestId=request_id or "unknown",
                    status="failed",
                    summary=payload_or_err,
                )

            return map_payload_to_response(payload_or_err, fallback_request_id=request_id)

        except Exception as e:
            return StampDataResponse(
                requestId=request_id or "unknown",
                status="failed",
                summary=f"Exception calling API: {e}",
            )
