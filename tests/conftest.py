import pytest
import structlog
from integritas_mcp_server.config import get_settings

# Configure logging for tests
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)

@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Override settings for all tests by setting environment variables."""
    monkeypatch.setenv("MINIMA_API_BASE", "https://upstream.example")
    # Clear the cache to ensure the new settings are loaded
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def log_test_name(request):
    """A fixture that automatically logs the name of the test being run."""
    logger = structlog.get_logger(__name__)
    logger.info(f"--- Starting test: {request.node.name} ---")