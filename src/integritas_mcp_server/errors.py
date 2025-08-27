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

def map_status_to_error(status: int, detail: str) -> MCPServerError:
    if status == 400:
        return InvalidInputError(detail)
    if status in (401, 403):
        return AuthError(detail)
    if status == 429:
        return RateLimitError(detail)
    if 500 <= status < 600:
        return TransientError(detail)
    return PermanentError(detail)
