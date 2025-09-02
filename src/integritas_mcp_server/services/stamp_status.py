from __future__ import annotations
from typing import Optional, Dict, Any, List
import asyncio
import structlog
from ..config import get_settings
from ..http_client import post_json
from ..errors import map_status_to_error, MCPServerError
from ..models import (
    StampStatusRequest,
    StampStatusResult,
    StampStatusResultSuccess,
    StampStatusResultPending,
    StampStatusResultError,
)

log = structlog.get_logger()

PATH_STAMP_STATUS = "/v1/timestamp/status/"
POLLING_INTERVAL_SECONDS = 5
MAX_ATTEMPTS = 6

async def _get_batch_stamp_status(
    uids: List[str], request_id: Optional[str], api_key: Optional[str]
) -> List[Dict[str, Any]]:
    """Makes a single batch POST request to the upstream API for the given UIDs."""
    s = get_settings()
    headers = {"x-request-id": request_id or "integritas-mcp"}
    if api_key:
        headers["x-api-key"] = api_key
    elif s.minima_api_key:
        headers["x-api-key"] = s.minima_api_key

    try:
        r = await post_json(PATH_STAMP_STATUS, json={"uids": uids}, headers=headers)

        if r.status_code >= 300:
            detail = r.text
            err = map_status_to_error(r.status_code, detail)
            log.warning("upstream_error_batch", status=r.status_code, detail=detail, uids=uids)
            raise err # Re-raise HTTP errors for the caller to handle

        payload = r.json()
        return payload.get("data", [])
    except MCPServerError as e:
        log.error("batch_request_mcp_error", error=str(e), uids=uids)
        raise # Re-raise for the caller to handle
    except Exception as e:
        log.error("batch_request_exception", error=str(e), uids=uids)
        raise MCPServerError(f"Batch request failed: {e}") from e


async def get_definitive_stamp_status(
    req: StampStatusRequest, request_id: Optional[str] = None, api_key: Optional[str] = None
) -> List[StampStatusResult]:
    """Fetches the status for all UIDs, polling until a definitive result for each."""
    # Initialize results with pending status for all requested UIDs
    current_results: Dict[str, StampStatusResult] = {
        uid: StampStatusResultPending(status=True, uid=uid, data="", number=0, datecreated="", onchain=False) # Placeholder
        for uid in req.uids
    }

    for attempt in range(MAX_ATTEMPTS):
        pending_uids_list = [
            uid for uid, result in current_results.items()
            if isinstance(result, StampStatusResultPending) and not result.onchain
        ]

        if not pending_uids_list:
            log.info("all_uids_resolved", attempt=attempt)
            break # All UIDs have been resolved

        log.info("polling_uids", uids=pending_uids_list, attempt=attempt + 1)

        try:
            # Always send all original UIDs in the request
            response_data_raw = await _get_batch_stamp_status(req.uids, request_id, api_key)

            for item_data in response_data_raw:
                uid_from_response = item_data.get("uid")
                if uid_from_response and uid_from_response in current_results:
                    # Apply user's specific logic for determining definitive status
                    if item_data.get("status") is False: # API returned status=False (error)
                        current_results[uid_from_response] = StampStatusResultError(uid=uid_from_response, error=item_data.get("error", "Unknown error"))
                    elif item_data.get("onchain") is True: # API returned onchain=True (success)
                        current_results[uid_from_response] = StampStatusResultSuccess(**item_data)
                    elif item_data.get("onchain") is False and item_data.get("proof") == "ERROR": # Specific error condition
                        current_results[uid_from_response] = StampStatusResultError(uid=uid_from_response, error=item_data.get("error", "Proof error"))
                    # Otherwise, if status is True and onchain is False (and not proof==ERROR), it remains pending

        except MCPServerError as e:
            log.error("polling_mcp_error", error=str(e), uids=pending_uids_list)
            # If the batch request itself failed, mark all currently pending UIDs as errors
            for uid in pending_uids_list:
                current_results[uid] = StampStatusResultError(uid=uid, error=f"Batch request failed: {e}")
            break # Stop polling on batch error
        except Exception as e:
            log.error("polling_exception", error=str(e), uids=pending_uids_list)
            for uid in pending_uids_list:
                current_results[uid] = StampStatusResultError(uid=uid, error=f"Polling exception: {e}")
            break # Stop polling on exception

        if attempt < MAX_ATTEMPTS - 1:
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

    return list(current_results.values())