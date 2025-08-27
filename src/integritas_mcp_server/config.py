# src/integritas_mcp_server/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")
    minima_api_base: str  # e.g., https://api.minima.example
    minima_api_key: str | None = None
    request_timeout_seconds: float = 15.0
    max_retries: int = 3
    log_level: str = "INFO"

@lru_cache
def get_settings() -> Settings:
    return Settings()

