from pydantic import BaseSettings, SecretStr

class Settings(BaseSettings):
    MCP_ACCESS_TOKEN: SecretStr
    INTEGRITAS_API_KEY: SecretStr | None = None  # your upstream API key, optional here

    class Config:
        env_file = ".env"             # optional; you can omit if using systemd/PM2 env
        env_file_encoding = "utf-8"

settings = Settings()
