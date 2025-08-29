#src\integritas_mcp_server\errors.py

from __future__ import annotations
from pydantic import BaseModel

class UpstreamError(BaseModel):
    code: str
    message: str

class MCPServerError(Exception):
    def __init__(self, message: str, *, upstream: UpstreamError | None = None):
        super().__init__(message)
        self.upstream = upstream

class InvalidInputError(MCPServerError): ...
class AuthError(MCPServerError): ...
class RateLimitError(MCPServerError): ...
class TransientError(MCPServerError): ...
class PermanentError(MCPServerError): ...

def _friendly_message(detail: str | None, status: int | None = None) -> str:
    text = (detail or "").strip()
    if text:
        return text
    if status is None:
        return "Upstream request failed (no detail provided)"
    if status == 408:
        return "Upstream request timed out"
    if status == 0:  # you can use 0 as a sentinel for connect errors
        return "Upstream API unreachable"
    return f"Upstream request failed with status {status}"

def map_status_to_error(status: int, detail: str) -> MCPServerError:
    msg = _friendly_message(detail, status)
    if status == 400:
        return InvalidInputError(msg)
    if status in (401, 403):
        return AuthError(msg)
    if status == 429:
        return RateLimitError(msg)
    if 500 <= status < 600:
        return TransientError(msg)
    return PermanentError(msg)
