from __future__ import annotations
from typing import Final
import base64
import re

_HEX_RE: Final = re.compile(r"^(0x)?[0-9a-fA-F]+$")

def _b64_to_hex(s: str) -> str:
    raw = base64.b64decode(s, validate=True)
    return raw.hex()

def normalize_hash(value: str) -> str:
    """
    Accept hex (with/without 0x) or base64. Return lowercase hex (no 0x).
    """
    v = value.strip()
    if _HEX_RE.match(v):
        return v[2:].lower() if v.lower().startswith("0x") else v.lower()
    return _b64_to_hex(v).lower()
