# src/integritas_mcp_server/services/health.py
import time
import httpx
from ..config import get_settings
from ..models import HealthResponse

async def check_health(x_request_id: str | None = None) -> HealthResponse:
    s = get_settings()
    headers = {}
    if s.minima_api_key:
        headers["x-api-key"] = s.minima_api_key
    if x_request_id:
        headers["x-request-id"] = x_request_id

    # Prefer a real health endpoint if your upstream has one; fall back to a cheap HEAD/GET.
    url = s.minima_api_health or f"{s.minima_api_base}/health"
    start = time.perf_counter()
    status = "ok"
    summary = "Healthy"
    reachable = True
    code = None
    latency = None

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url, headers=headers)  # use .head(...) if supported
            code = r.status_code
            latency = int((time.perf_counter() - start) * 1000)
            if r.status_code >= 300:
                status, summary = "degraded", f"Upstream returned {r.status_code}"
    except Exception as e:
        reachable = False
        status, summary = "down", f"Upstream error: {e.__class__.__name__}"

    return HealthResponse(
        status=status,
        upstream_reachable=reachable,
        upstream_status=code,
        upstream_latency_ms=latency,
        summary=summary,
    )
