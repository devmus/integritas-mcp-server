# # # src/integritas_mcp_server/services/health.py
# import time
# import httpx
# from typing import Literal # Import Literal
# from ..config import get_settings
# from ..models import HealthResponse
# import structlog
# log = structlog.get_logger()

# async def check_readiness(x_request_id: str | None = None, api_key: str | None = None) -> HealthResponse:
#     s = get_settings()
#     headers: dict[str, str] = {}

#     if api_key is not None:
#         headers["x-api-key"] = api_key
#     elif s.minima_api_key:
#         headers["x-api-key"] = s.minima_api_key

#     if x_request_id:
#         headers["x-request-id"] = x_request_id

#     url = s.minima_api_health
#     start = time.perf_counter()

#     # Explicitly type status
#     status: Literal["ok", "degraded", "down"] = "ok"
#     summary = "Ready"
#     reachable = True
#     code: int | None = None

#     # try:
#     #     if url is None: # Handle None URL case
#     #         reachable = False
#     #         status = "down"
#     #         summary = "Upstream health URL not configured"
#     #     else:
#     #         async with httpx.AsyncClient(timeout=5) as client:
#     #             r = await client.get(url, headers=headers)
#     #             log.debug("Actual request headers", headers=dict(r.request.headers))
#     #             code = r.status_code
#     #             if r.status_code >= 300:
#     #                 status = "degraded"
#     #                 summary = f"Upstream returned {r.status_code}"
#     # except Exception as e:
#     #     reachable = False
#     #     status = "down"
#     #     summary = f"Upstream error: {e.__class__.__name__}"

#     # latency_ms = int((time.perf_counter() - start) * 1000)

#     # return HealthResponse(
#     #     status=status,
#     #     upstream_reachable=reachable,
#     #     upstream_status=code,
#     #     upstream_latency_ms=latency_ms,
#     #     summary=summary,
#     # )

#     try:
#         if url is None:
#             reachable = False
#             status = "down"
#             summary = "Upstream health URL not configured"
#         else:
#             async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
#                 r = await client.get(url, headers=headers)
#                 # ---- SAFE LOGGING (won't raise) ----
#                 try:
#                     header_keys = list(r.request.headers.keys())
#                     log.debug("request_headers", header_keys=header_keys)
#                 except Exception:
#                     # Fall back silently if anything odd happens
#                     log.debug("request_headers_unavailable")
#                 # ------------------------------------

#                 code = r.status_code
#                 if code >= 300:
#                     status = "degraded"
#                     summary = f"Upstream returned {code}"
#                 else:
#                     status = "ok"
#                     summary = "Ready"
#     except Exception as e:
#         reachable = False
#         status = "down"
#         summary = f"Upstream error: {e.__class__.__name__}"

#     latency_ms = int((time.perf_counter() - start) * 1000)
#     return HealthResponse(
#         status=status,
#         upstream_reachable=reachable,
#         upstream_status=code,
#         upstream_latency_ms=latency_ms,
#         summary=summary,
#     )

# src/integritas_mcp_server/services/health.py
import time
import httpx
from typing import Literal
from ..config import get_settings
from ..models import HealthResponse

def _as_str(v):
    # Convert SecretStr or any object with get_secret_value() to plain str
    if hasattr(v, "get_secret_value"):
        try:
            return str(v.get_secret_value())
        except Exception:
            return str(v)
    return str(v)

async def check_readiness(
    x_request_id: str | None = None,
    api_key: str | None = None,
) -> HealthResponse:
    s = get_settings()

    headers: dict[str, str] = {}
    key = api_key or s.minima_api_key
    if key:
        headers["x-api-key"] = _as_str(key)
    if x_request_id:
        headers["x-request-id"] = x_request_id

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