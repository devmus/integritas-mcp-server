# src/integritas_mcp_server/services/stamp.py
from __future__ import annotations
from typing import Optional, Any, Dict
import structlog
from ..config import get_settings
from ..http_client import post_json
from ..errors import map_status_to_error
from ..models import StampResponse

log = structlog.get_logger()

# Single source of truth for the upstream path
PATH_STAMP = "/v1/timestamp/post"

def _pick(d: Dict[str, Any], *keys: str):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return None

def _parse_payload(payload: Dict[str, Any]) -> StampResponse:
    # Ensure 'inner' is always a Dict[str, Any]
    inner: Dict[str, Any]
    data_from_payload = payload.get("data")

    if isinstance(data_from_payload, dict):
        inner = data_from_payload
    else:
        # If 'data' is not a dict, or not present, use the top-level payload
        # We assume payload itself is a dict due to r.json()
        inner = payload

    uid = _pick(inner, "uid")

    stamped_at = (
        _pick(payload, "timestamp")
    )
    
    summary = payload.get("message") or (f"Stamp accepted (uid={uid})" if uid else "Stamp accepted")

    return StampResponse(uid=uid, stamped_at=stamped_at, summary=summary)

async def stamp(hash_hex: str, request_id: Optional[str] = None, api_key: str | None = None) -> StampResponse:
    s = get_settings()
    headers = {"x-request-id": request_id or "integritas-mcp", "content-type": "application/json"}
    # if s.minima_api_key:
    #     headers["x-api-key"] = s.minima_api_key
    # Prefer per-request key from tool args; else fall back to env
    if api_key is not None and isinstance(api_key, str):
        headers["x-api-key"] = api_key
    elif s.minima_api_key:
        headers["x-api-key"] = s.minima_api_key

    r = await post_json(PATH_STAMP, json={"hash": hash_hex}, headers=headers)

    if r.status_code >= 300:
        detail = r.text
        err = map_status_to_error(r.status_code, detail)
        log.warning("upstream_error", status=r.status_code, detail=detail)
        raise err  # subclasses MCPServerError

    payload = r.json()
    return _parse_payload(payload)
