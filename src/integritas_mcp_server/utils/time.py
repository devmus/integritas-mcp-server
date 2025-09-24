# src/integritas_mcp_server/utils/time.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Union

def utc_iso(dt: Optional[Union[datetime, str]] = None) -> str:
    """
    Return ISO-8601 UTC (Z-suffixed).
    - If input is a string, return it as-is (assumed ISO).
    - If input is None, use now().
    """
    if isinstance(dt, str):
        return dt
    return (dt or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
