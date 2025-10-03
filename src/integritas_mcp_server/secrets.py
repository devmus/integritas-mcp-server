# secrets.py
from typing import Optional
import os
import keyring
from .config import get_settings  # <-- import settings

SERVICE_NAME = "integritas-mcp"
ACCOUNT = "integritas_api_key"

_memory_key: Optional[str] = None

def set_api_key_memory(key: str) -> None:
    global _memory_key
    _memory_key = key

def clear_api_key_memory() -> None:
    global _memory_key
    _memory_key = None

def save_api_key_keyring(key: str) -> None:
    keyring.set_password(SERVICE_NAME, ACCOUNT, key)

def load_api_key_keyring() -> Optional[str]:
    try:
        return keyring.get_password(SERVICE_NAME, ACCOUNT)
    except Exception:
        return None

def clear_api_key_keyring() -> None:
    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNT)
    except Exception:
        pass

def resolve_api_key() -> Optional[str]:
    """
    Order:
      1) in-memory (auth_set_api_key)
      2) keyring
      3) Settings (.env): minima_api_key (accepts MINIMA_API_KEY or INTEGRITAS_API_KEY)
      4) raw env var INTEGRITAS_API_KEY (last-ditch)
    """
    if _memory_key:
        return _memory_key

    k = load_api_key_keyring()
    if k:
        return k

    s = get_settings()
    if getattr(s, "minima_api_key", None):
        return str(s.minima_api_key)

    return os.getenv("INTEGRITAS_API_KEY")
