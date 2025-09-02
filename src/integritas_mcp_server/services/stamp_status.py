# src/integritas_mcp_server/services/stamp_status.py
from __future__ import annotations
from typing import Optional
import asyncio
import structlog
from ..config import get_settings
from ..http_client import get_json
from ..errors import map_status_to_error
from ..models import (
    StampStatusRequest,
    StampStatusResult,
    StampStatusResultSuccess,
    StampStatusResultError,
)

log = structlog.get_logger()

# This would be the real upstream API path
PATH_STAMP_STATUS = "/v1/uid/status/{uid}"
POLLING_INTERVAL_SECONDS = 10
MAX_ATTEMPTS = 12  # 12 attempts * 10 seconds = 2 minutes timeout


async def _get_single_uid_status(
    uid: str, request_id: Optional[str], api_key: Optional[str]
) -> StampStatusResult:
    """Fetches the status for a single UID, polling until a definitive result."""
    s = get_settings()
    headers = {"x-request-id": request_id or "integritas-mcp"}
    if api_key:
        headers["x-api-key"] = api_key
    elif s.minima_api_key:
        headers["x-api-key"] = s.minima_api_key

    path = PATH_STAMP_STATUS.format(uid=uid)

    for attempt in range(MAX_ATTEMPTS):
        r = await get_json(path, headers=headers)

        if r.status_code >= 300:
            # For a persistent error like 404, we can fail fast.
            if r.status_code == 404:
                log.warning("uid_not_found", uid=uid, status=r.status_code)
                return StampStatusResultError(uid=uid, error="UID not found")
            # For other errors, we might retry, but for now, we'll fail.
            detail = r.text
            err = map_status_to_error(r.status_code, detail)
            log.warning("upstream_error", uid=uid, status=r.status_code, detail=detail)
            # Not raising, but returning an error model in the list
            return StampStatusResultError(uid=uid, error=str(err))

        payload = r.json().get("data", [{}])[0]

        if payload.get("onchain"):
            return StampStatusResultSuccess(**payload)
        
        if payload.get("status"):
            
             # It's a valid pending status, continue polling
            log.info("uid_pending", uid=uid, attempt=attempt + 1)
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
        else:
            # The response indicates an error within the data payload
            error_message = payload.get("error", "Unknown error")
            log.warning("uid_error_payload", uid=uid, payload=payload)
            return StampStatusResultError(uid=uid, error=error_message)

    # If the loop finishes without returning, it timed out
    log.warning("uid_polling_timeout", uid=uid)
    return StampStatusResultError(uid=uid, error="Polling timed out after {} seconds".format(MAX_ATTEMPTS * POLLING_INTERVAL_SECONDS))


async def perform_stamp_status(
    req: StampStatusRequest, request_id: Optional[str] = None, api_key: Optional[str] = None
) -> list[StampStatusResult]:
    """Concurrently fetches the status for all UIDs in the request."""
    tasks = [
        _get_single_uid_status(uid, request_id, api_key) for uid in req.uids
    ]
    results = await asyncio.gather(*tasks)
    return results
