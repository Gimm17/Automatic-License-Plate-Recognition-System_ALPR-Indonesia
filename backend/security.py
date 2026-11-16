"""
backend/security.py
Small API-key guard for demo/internal deployments.
"""

from typing import Optional

from fastapi import Header, HTTPException, WebSocket

from config import settings


def _api_key_enabled() -> bool:
    return bool(settings.API_REQUIRE_KEY)


def _valid_key(value: Optional[str]) -> bool:
    return bool(settings.API_KEY) and value == settings.API_KEY


def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    """FastAPI dependency that enforces X-API-Key when enabled."""
    if not _api_key_enabled():
        return None
    if _valid_key(x_api_key):
        return None
    raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def verify_websocket_api_key(websocket: WebSocket) -> bool:
    """Validate WebSocket query api_key before starting a stream."""
    if not _api_key_enabled():
        return True
    return _valid_key(websocket.query_params.get("api_key"))
