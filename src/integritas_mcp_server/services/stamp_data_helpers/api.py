# services/stamp_data_helpers/api.py
import aiohttp
from typing import Any, Dict, Optional
from ...config import get_settings

s = get_settings()
API_BASE_URL = s.minima_api_base.rstrip("/")

def build_headers(possible_secret: Optional[Any], fallback: Optional[str]) -> Dict[str, str]:
    """
    Accepts either a plain string, a Pydantic SecretStr (with get_secret_value),
    or None. Falls back to `fallback` if needed.
    """
    key: Optional[str] = None

    if possible_secret is not None:
        getter = getattr(possible_secret, "get_secret_value", None)
        if callable(getter):
            try:
                key = getter()  # SecretStr
            except Exception:
                key = None
        if key is None:
            # plain str or any other type -> stringize
            key = str(possible_secret)

    if not key and fallback:
        key = fallback

    return {"x-api-key": key} if key else {}

async def post_multipart(
    session: aiohttp.ClientSession,
    url: str,
    form: aiohttp.FormData,
    headers: Dict[str, str],
):
    """
    Posts multipart form; returns JSON payload dict or error string.
    Tries to close any file-like objects attached to the form.
    """
    try:
        async with session.post(url, data=form, headers=headers) as resp:
            if resp.status < 200 or resp.status >= 300:
                text = await resp.text()
                return f"API error {resp.status}: {text}"
            return await resp.json()
    finally:
        # Best-effort close of file-like values
        try:
            fields = getattr(form, "_fields", None)
            if fields:
                for field in fields:
                    val = getattr(field, "value", None)
                    close = getattr(val, "close", None)
                    if callable(close):
                        try:
                            close()
                        except Exception:
                            pass
        except Exception:
            pass
