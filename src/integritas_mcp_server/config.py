# src/integritas_mcp_server/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    minima_api_base: str
    minima_api_key: str

    class Config:
        env_file = ".env"  # path relative to project root

settings = Settings()
