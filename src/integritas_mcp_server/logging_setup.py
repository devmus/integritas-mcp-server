# import logging
# import sys
# import structlog
# from .config import get_settings

# def setup_logging():
#     level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
#     logging.basicConfig(stream=sys.stdout, level=level)
#     structlog.configure(
#         processors=[
#             structlog.processors.TimeStamper(fmt="iso"),
#             structlog.processors.add_log_level,
#             structlog.processors.JSONRenderer(),
#         ],
#         logger_factory=structlog.stdlib.LoggerFactory(),
#         wrapper_class=structlog.stdlib.BoundLogger,
#     )


# src/integritas_mcp_server/logging_setup.py
import sys, logging, structlog

def setup_logging():
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    structlog.configure(logger_factory=structlog.PrintLoggerFactory(file=sys.stderr))
    # optional: quiet noisy libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anyio").setLevel(logging.WARNING)