# services/stamp_data_helpers/status.py
from typing import Optional

def map_status(api_status: Optional[str]) -> str:
    s = (api_status or "").lower()
    if s in {"success", "ok", "completed", "complete"}:
        return "finalized"
    if s in {"pending", "processing", "queued"}:
        return "pending"
    if s in {"failed", "error"}:
        return "failed"
    return s or "unknown"
