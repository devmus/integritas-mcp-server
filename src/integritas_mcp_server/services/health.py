# # src/integritas_mcp_server/services/health.py
import time
import httpx
from ..config import get_settings
from ..models import HealthResponse
import structlog
log = structlog.get_logger()

async def check_readiness(x_request_id: str | None = None, api_key: str | None = None) -> HealthResponse:
    s = get_settings()
    headers: dict[str, str] = {}

    if api_key is not None:
        headers["x-api-key"] = api_key
    elif s.minima_api_key:
        headers["x-api-key"] = s.minima_api_key

    if x_request_id:
        headers["x-request-id"] = x_request_id

    url = s.minima_api_health
    start = time.perf_counter()

    status = "ok"
    summary = "Ready"
    reachable = True
    code: int | None = None

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url, headers=headers)
            log.debug("Actual request headers", headers=dict(r.request.headers))
            code = r.status_code
            if r.status_code >= 300:
                status = "degraded"
                summary = f"Upstream returned {r.status_code}"
    except Exception as e:
        reachable = False
        status = "down"
        summary = f"Upstream error: {e.__class__.__name__}"

    latency_ms = int((time.perf_counter() - start) * 1000)

    return HealthResponse(
        status=status,
        upstream_reachable=reachable,
        upstream_status=code,
        upstream_latency_ms=latency_ms,
        summary=summary,
    )
