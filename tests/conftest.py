# tests/conftest.py
import os
import pytest
from integritas_mcp_server.config import get_settings

@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch):
    # Set a default baseline for tests (can be overridden per test)
    monkeypatch.setenv("MINIMA_API_BASE", "https://upstream.example")
    monkeypatch.delenv("MINIMA_API_KEY", raising=False)
    # Clear cached settings so env changes take effect
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
