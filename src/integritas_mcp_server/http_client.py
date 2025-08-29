# src/integritas_mcp_server/http_client.py
from __future__ import annotations
import asyncio, httpx, time, uuid
import httpx
import structlog
from typing import Any
from .config import get_settings
from .errors import TransientError

log = structlog.get_logger()

DEFAULT_TIMEOUT = 5.0        # seconds
RETRIES = 2                  # total attempts = RETRIES + 1
BACKOFF = 0.2                # seconds, simple linear backoff

class NetworkError(Exception): ...

SENSITIVE_KEYS = {"authorization", "x-api-key", "api_key", "token", "secret"}

def _redact(obj: Any):
    if isinstance(obj, dict):
        return {k: ("***" if k.lower() in SENSITIVE_KEYS else _redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj

def _body_preview(resp: httpx.Response, limit: int = 2000) -> Any:
    ctype = (resp.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        try:
            return _redact(resp.json())
        except Exception:
            # fall through to text preview
            pass
    # Non-JSON or JSON parse failed: return truncated text
    txt = resp.text
    return txt if len(txt) <= limit else (txt[:limit] + f"... (+{len(txt)-limit} bytes)")

async def get_json(path: str, *, x_request_id: str | None = None, headers: dict[str, str] | None = None):
    s = get_settings()
    base = s.minima_api_base.rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    hdrs: dict[str, str] = {}
    if headers:
        hdrs.update(headers)
    if s.minima_api_key:
        hdrs.setdefault("x-api-key", s.minima_api_key)
    hdrs.setdefault("x-request-id", x_request_id or f"integritas-http-{uuid.uuid4().hex[:8]}")

    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        for attempt in range(RETRIES + 1):
            try:
                resp = await client.get(url, headers=hdrs)
                return resp
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                last_exc = e
                if attempt == RETRIES:
                    raise
                await asyncio.sleep(BACKOFF * (attempt + 1))
    # Shouldn't get here; keep mypy happy
    raise last_exc or RuntimeError("get_json fell through")

async def post_json(path: str, json: dict, headers: dict[str, str]) -> httpx.Response:
    s = get_settings()  # read at call time (honors env overrides in tests)
    base = s.minima_api_base.rstrip("/")
    url_path = path if path.startswith("/") else f"/{path}"
    full_url = f"{base}{url_path}"

    attempt = 0
    delay = 0.2
    while True:
        attempt += 1
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(s.request_timeout_seconds)) as client:
                log.info("upstream_request", method="POST", url=full_url)
                resp = await client.post(full_url, json=json, headers=headers)
                log.info("upstream_response", status=resp.status_code, url=full_url)
                # Log body only at DEBUG, or always for errors
                if resp.status_code >= 400:
                    log.info("upstream_response_body", body=_body_preview(resp))
                else:
                    log.info("upstream_response_body", body=_body_preview(resp))
                return resp
        # except (httpx.TransportError, httpx.ReadTimeout) as e:
        #     if attempt >= s.max_retries:
        #         log.warning("upstream_transport_error", error=str(e), url=full_url, attempt=attempt)
        #         raise
        #     log.warning("upstream_retrying", error=str(e), url=full_url, attempt=attempt, delay=delay)
        #     await asyncio.sleep(delay)
        #     delay = min(delay * 2, 2.0)
        # except Exception as e:
        #     log.exception("upstream_unexpected_error")
        #     raise NetworkError(str(e)) from e
        except (httpx.TransportError, httpx.ReadTimeout) as e:
            # Make the error text useful
            err_repr = repr(e)
            if attempt >= s.max_retries:
                log.warning("upstream_transport_error", error=err_repr, url=full_url, attempt=attempt)
                # Map common timeout types to friendly messages
                if isinstance(e, httpx.ConnectTimeout):
                    raise TransientError("Upstream API unreachable (connect timeout)") from e
                if isinstance(e, httpx.ReadTimeout):
                    raise TransientError("Upstream request timed out") from e
                raise TransientError(f"Upstream transport error: {err_repr}") from e

            log.warning("upstream_retrying", error=err_repr, url=full_url, attempt=attempt, delay=delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 2.0)

        except Exception as e:
            log.exception("upstream_unexpected_error")
            # Ensure this is never blank
            raise NetworkError(repr(e)) from e