# # src/integritas_mcp_server/services/stamp_data_helpers/upload.py
# import os, aiohttp, pathlib

# async def form_from_file_path(path: str, contentType: str):
#     if not path:
#         raise ValueError("file_path is required")
#     p = pathlib.Path(path)
#     if not p.exists() or not p.is_file():
#         raise FileNotFoundError(f"file_path not found: {path}")

#     f = open(path, "rb")  # binary
#     form = aiohttp.FormData()
#     form.add_field(
#         "file",
#         f,
#         filename=p.name,
#         content_type=contentType, 
#     )
#     # return a cleanup callable so caller can close the file handle
#     return form, f.close

# async def form_from_file_url(session: aiohttp.ClientSession, url: str, contentType: str):
#     if not url:
#         raise ValueError("file_url is required")
#     async with session.get(str(url)) as r:
#         if r.status >= 400:
#             body = await r.text()
#             raise RuntimeError(f"download failed {r.status}: {body[:200]}")
#         data = await r.read()
#     form = aiohttp.FormData()
#     form.add_field("file", data, filename="upload.bin", content_type=contentType)
#     return form  # no cleanup needed

# src/integritas_mcp_server/services/stamp_data_helpers/upload.py
import os, aiohttp, pathlib
from typing import Callable, Tuple, Dict, Any, Callable, Tuple, Union, Optional
import inspect

async def maybe_await(value):
    return await value if inspect.isawaitable(value) else value

def normalize_form_result(
    res: Union[aiohttp.FormData, Tuple[aiohttp.FormData, Optional[Callable[[], None]]]]
) -> Tuple[aiohttp.FormData, Optional[Callable[[], None]]]:
    if isinstance(res, tuple):
        form, cleanup = res
        return form, cleanup
    return res, None

async def form_from_file_path(path: str, content_type: str = "application/octet-stream") -> tuple[aiohttp.FormData, Callable[[], None]]:
    if not path:
        raise ValueError("file_path is required")
    p = pathlib.Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"file_path not found: {path}")

    f = open(path, "rb")
    form = aiohttp.FormData()
    form.add_field(
        "file",
        f,
        filename=p.name,
        content_type=content_type,
    )
    return form, f.close

async def form_from_file_url(session: aiohttp.ClientSession, url: str, content_type: str = "application/octet-stream") -> aiohttp.FormData:
    async with session.get(str(url)) as r:
        r.raise_for_status()
        data = await r.read()
    form = aiohttp.FormData()
    form.add_field("file", data, filename="upload.bin", content_type=content_type)
    return form
