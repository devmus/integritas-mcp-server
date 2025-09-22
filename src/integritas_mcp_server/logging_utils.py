# src/integritas_mcp_server/logging_utils.py
from __future__ import annotations
from typing import Any, Callable, Optional
import functools, json
from .logging_setup import get_logger

log = get_logger()

def _safe_json(v: Any, limit: int = 2000) -> Any:
    try:
        s = json.dumps(v, default=str)  # ensure_ascii defaults to True
        return (s[:limit] + "...") if len(s) > limit else s
    except Exception:
        return (str(v)[:limit] + "...")

def tool_logger(fn: Callable):
    """Decorator to log tool start/success/error with req_id correlation."""
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        # ctx is either kwarg or second positional (mcp.fastmcp style)
        ctx = kwargs.get("ctx") or (args[1] if len(args) > 1 else None)
        req_id = getattr(ctx, "request_id", None) if ctx else None

        # Log inputs (truncate)
        log.info(
            "tool_start",
            tool=fn.__name__,
            req_id=req_id,
            kwargs=_safe_json({k: v for k, v in kwargs.items() if k != "ctx"})
        )
        try:
            res = await fn(*args, **kwargs)
            # avoid dumping huge models
            out = getattr(res, "model_dump", None)
            payload = out() if callable(out) else res
            log.info(
                "tool_success",
                tool=fn.__name__,
                req_id=req_id,
                result=_safe_json(payload)
            )
            return res
        except Exception as e:
            log.exception("tool_error", tool=fn.__name__, req_id=req_id, err=str(e))
            raise
    return wrapper
