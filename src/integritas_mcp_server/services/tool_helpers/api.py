# services/stamp_data_helpers/api.py
import aiohttp
from typing import Any, Dict, Optional
from ...config import get_settings
import re

s = get_settings()
API_BASE_URL = s.minima_api_base.rstrip("/")

_HEX_RE = re.compile(r"^(0x)?[0-9a-fA-F]+$")

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

# async def post_multipart(
#     session: aiohttp.ClientSession,
#     url: str,
#     form: aiohttp.FormData,
#     headers: Dict[str, str],
# ):
#     """
#     Posts multipart form; returns JSON payload dict or error string.
#     Tries to close any file-like objects attached to the form.
#     """
#     try:
#         async with session.post(url, data=form, headers=headers) as resp:
#             if resp.status < 200 or resp.status >= 300:
#                 text = await resp.text()
#                 return f"API error {resp.status}: {text}"
#             return await resp.json()
#     finally:
#         # Best-effort close of file-like values
#         try:
#             fields = getattr(form, "_fields", None)
#             if fields:
#                 for field in fields:
#                     val = getattr(field, "value", None)
#                     close = getattr(val, "close", None)
#                     if callable(close):
#                         try:
#                             close()
#                         except Exception:
#                             pass
#         except Exception:
#             pass

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
