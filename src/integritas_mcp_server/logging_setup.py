# # src/integritas_mcp_server/logging_setup.py
# import sys, logging, structlog

# def setup_logging():
#     logging.basicConfig(level=logging.INFO, stream=sys.stderr)
#     structlog.configure(logger_factory=structlog.PrintLoggerFactory(file=sys.stderr))
#     # optional: quiet noisy libs
#     logging.getLogger("httpx").setLevel(logging.WARNING)
#     logging.getLogger("anyio").setLevel(logging.WARNING)

# src/integritas_mcp_server/logging_setup.py
import sys, logging, structlog
from typing import Any, Dict

SENSITIVE = {"authorization", "x-api-key", "api_key", "token"}

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

def setup_logging():
    # stdlib logging -> INFO to stderr
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(message)s",  # let structlog format
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            # redact dict-like event payloads
            lambda logger, method, event_dict: _redact(event_dict),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    # quiet noisy deps if you like
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anyio").setLevel(logging.WARNING)

def get_logger():
    return structlog.get_logger("integritas-mcp-server")
