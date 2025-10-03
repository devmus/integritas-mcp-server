# services/stamp_data_helpers/api.py
import aiohttp
from typing import Any, Dict, Optional
from ...config import get_settings
from ...secrets import resolve_api_key

s = get_settings()
API_BASE_URL = s.minima_api_base.rstrip("/")

def build_headers(possible_secret: Optional[Any], fallback: Optional[str]) -> Dict[str, str]:
    """
    Accepts either a plain string, a Pydantic SecretStr (with get_secret_value),
    or None. Falls back to `fallback`, then to the hybrid provider
    (memory -> keyring -> env var).
    """
    key: Optional[str] = None

    # 1) request-supplied (SecretStr or str)
    if possible_secret is not None:
        getter = getattr(possible_secret, "get_secret_value", None)
        if callable(getter):
            try:
                key = getter()  # SecretStr
            except Exception:
                key = None
        if key is None:
            try:
                key = str(possible_secret)
            except Exception:
                key = None

    # 2) explicit function arg
    if not key and fallback:
        key = fallback

    # 3) global provider
    if not key:
        key = resolve_api_key()

    return {"x-api-key": key} if key else {}

async def post_json(
    session: aiohttp.ClientSession,
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
):
    """
    Posts JSON; returns JSON payload dict or error string.
    """
    merged = {"Content-Type": "application/json", **headers}
    async with session.post(url, json=payload, headers=merged) as resp:
        if resp.status < 200 or resp.status >= 300:
            text = await resp.text()
            return f"API error {resp.status}: {text}"
        return await resp.json()

# src/integritas_mcp_server/services/stamp_data_helpers/api.py
import aiohttp
from typing import Dict, Union, Any

async def post_multipart(
    session: aiohttp.ClientSession,
    url: str,
    form: aiohttp.FormData,
    headers: Dict[str, str],
) -> Union[Dict[str, Any], str]:
    try:
        # ✅ Always pass the FormData; do NOT write "form or False"
        async with session.post(url, data=form, headers=headers) as resp:
            text = await resp.text()
            try:
                return await resp.json()
            except Exception:
                # return text so caller can surface upstream error body
                return text
    except Exception as e:
        return f"{type(e).__name__}: {e}"
