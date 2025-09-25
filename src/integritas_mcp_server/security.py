from __future__ import annotations
from typing import Callable, Awaitable
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import PlainTextResponse
from starlette import status

def _get_header(scope: Scope, name: bytes) -> bytes | None:
    # headers are lower-cased by Starlette/Uvicorn
    for k, v in scope.get("headers") or []:
        if k == name:
            return v
    return None

class BearerGuard:
    """
    Simple ASGI middleware that enforces Authorization: Bearer <token>
    on HTTP requests. (SSE uses HTTP, so it’s covered.)
    """
    def __init__(self, app: ASGIApp, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only protect HTTP traffic (including SSE). Ignore lifespan, etc.
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Allow a minimal health check path to be unauthenticated if you want.
        path = scope.get("path") or ""
        if path == "/healthz":
            return await self.app(scope, receive, send)

        auth = _get_header(scope, b"authorization")
        if not auth or not auth.lower().startswith(b"bearer "):
            res = PlainTextResponse(
                "missing bearer", status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": 'Bearer realm="mcp"'}
            )
            return await res(scope, receive, send)

        provided = auth.split(None, 1)[1].decode("utf-8")
        if not provided or provided != self.token:
            res = PlainTextResponse(
                "invalid token", status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'}
            )
            return await res(scope, receive, send)

        return await self.app(scope, receive, send)
