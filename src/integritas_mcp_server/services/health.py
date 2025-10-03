# src/integritas_mcp_server/services/health.py
import time
import httpx
from typing import Optional, Literal
from ..config import get_settings
from ..models import HealthResponse
from ..secrets import resolve_api_key
from .tool_helpers.api import build_headers

def _as_str(v):
    # Convert SecretStr or any object with get_secret_value() to plain str
    if hasattr(v, "get_secret_value"):
        try:
            return str(v.get_secret_value())
        except Exception:
            return str(v)
    return str(v)

# ----- main entrypoint ---------------------------------------------------------

async def check_readiness(
    req,
    request_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> HealthResponse:
    s = get_settings()

    rid = request_id or "unknown"

    headers = build_headers(req.api_key, api_key)
    if not headers.get("x-api-key"):
        return HealthResponse(
            status="down",
            upstream_reachable=False,
            upstream_status=None,
            upstream_latency_ms=0,
            summary="No API key configured. Set INTEGRITAS_API_KEY in .env or run auth_set_api_key."
        )

    url = s.minima_api_health

    start = time.perf_counter()

    status: Literal["ok", "degraded", "down"] = "ok"
    summary = "Ready"
    reachable = True
    code: int | None = None

    try:
        if not url:
            reachable = False
            status = "down"
            summary = "Upstream health URL not configured"
        else:
            # cast to str in case url is a pydantic HttpUrl
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(str(url), headers=headers)
            code = r.status_code
            if code >= 300:
                status = "degraded"
                summary = f"Upstream returned {code}"
            else:
                status = "ok"
                summary = "Ready"
    except Exception as e:
        reachable = False
        status = "down"
        # include message to make diagnosing easier next time
        summary = f"Upstream error: {e.__class__.__name__}: {e}"

    latency_ms = int((time.perf_counter() - start) * 1000)
    return HealthResponse(
        status=status,
        upstream_reachable=reachable,
        upstream_status=code,
        upstream_latency_ms=latency_ms,
        summary=summary,
    )