# tools_auth.py (fixed)
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .secrets import (
    set_api_key_memory, clear_api_key_memory,
    save_api_key_keyring, resolve_api_key, clear_api_key_keyring,
)

MASK = "••••••"

def _mask(value: str, keep: int = 4) -> str:
    if not value:
        return ""
    return (MASK * max(0, len(value) - keep)) + value[-keep:]

class SetApiKeyInput(BaseModel):
    api_key: str = Field(..., min_length=8, description="Your upstream API key")

class GenericResult(BaseModel):
    ok: bool
    summary: str
    preview: Optional[str] = None

def auth_set_api_key(args: Dict[str, Any]) -> Dict[str, Any]:
    payload = SetApiKeyInput(**args)
    key = payload.api_key.strip()

    # Memory (immediate) + keyring (persistence)
    set_api_key_memory(key)
    try:
        save_api_key_keyring(key)
    except Exception:
        # still fine this session via memory
        pass

    return GenericResult(
        ok=True,
        summary="API key saved securely.",
        preview=_mask(key),
    ).model_dump()

def auth_get_api_key(_: Dict[str, Any]) -> Dict[str, Any]:
    key = resolve_api_key() or ""
    return GenericResult(
        ok=bool(key),
        summary="API key is configured." if key else "No API key found.",
        preview=_mask(key) if key else None,
    ).model_dump()

def auth_clear_api_key(_: Dict[str, Any]) -> Dict[str, Any]:
    clear_api_key_memory()
    clear_api_key_keyring()
    return GenericResult(
        ok=True,
        summary="API key cleared from memory and keyring.",
    ).model_dump()
