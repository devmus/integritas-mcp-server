# src/integritas_mcp_server/logging_setup.py
import sys, logging, structlog
from typing import Any, Dict

SENSITIVE = {"authorization", "x-api-key", "api_key", "token", "cookie", "set-cookie", "x-auth-token"}


def redact_processor(logger, method, event_dict):
    return _redact(event_dict)

def _redact(mapping: Dict[str, Any]):
    out = {}
    for k, v in mapping.items():
        if isinstance(v, dict):
            v = _redact(v)
        if isinstance(k, str) and k.lower() in SENSITIVE:
            out[k] = "[REDACTED]"
        else:
            out[k] = v
    return out

def _force_utf8_stdio():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            except Exception:
                pass

def setup_logging():
    _force_utf8_stdio()
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            redact_processor,
            structlog.processors.JSONRenderer(ensure_ascii=True),  # JSON to STDERR
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anyio").setLevel(logging.WARNING)

def get_logger():
    return structlog.get_logger("integritas-mcp-server")