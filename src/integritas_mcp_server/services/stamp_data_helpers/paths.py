# services/stamp_data_helpers/paths.py
import os
from urllib.parse import urlparse, unquote
from typing import Optional

def to_local_path(path_or_uri: Optional[str]) -> Optional[str]:
    if not path_or_uri:
        return None
    if isinstance(path_or_uri, str) and path_or_uri.startswith("file://"):
        u = urlparse(path_or_uri)
        if u.netloc:  # UNC/Windows share
            return f"//{u.netloc}{unquote(u.path)}"
        return unquote(u.path)
    return path_or_uri

def safe_basename(p: str, default: str = "upload.bin") -> str:
    try:
        name = os.path.basename(p)
        return name or default
    except Exception:
        return default
