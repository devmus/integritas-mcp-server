# services/stamp_data_helpers/upload.py
import os
import aiohttp
from aiohttp import FormData
from typing import Tuple, Union
from .paths import to_local_path, safe_basename

async def form_from_file_url(session: aiohttp.ClientSession, file_url: str) -> FormData:
    async with session.get(file_url) as r:
        if r.status < 200 or r.status >= 300:
            text = await r.text()
            raise RuntimeError(f"Could not fetch file_url ({r.status}): {text}")
        content = await r.read()
        ct = r.headers.get("Content-Type") or "application/octet-stream"

    # filename best-effort (path part only)
    filename = safe_basename(file_url)

    form = FormData()
    form.add_field("file", content, filename=filename, content_type=ct)
    return form

def form_from_file_path(file_path: str) -> Tuple[bool, Union[FormData, str]]:
    """
    Returns (True, FormData) or (False, error_message).
    """
    local_path = to_local_path(file_path)
    if not local_path:
        return False, "file_path was empty."
    if not os.path.isfile(local_path):
        return False, f"File not found: {file_path}"

    f = open(local_path, "rb")
    form = FormData()
    # aiohttp will close the file when request ends; but to be explicit:
    # we attach the file object; caller's post helper should close on exit.
    form.add_field(
        "file",
        f,
        filename=os.path.basename(local_path),
        content_type="application/octet-stream",
    )
    return True, form
