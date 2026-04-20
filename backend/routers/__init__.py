"""backend/routers/__init__.py"""
from .detection import router as detection_router
from .cameras import router as cameras_router
from .vehicles import router as vehicles_router
from .stats import router as stats_router
from .export import router as export_router
from .stream import ws_router, api_router as stream_api_router

__all__ = [
    "detection_router",
    "cameras_router",
    "vehicles_router",
    "stats_router",
    "export_router",
    "ws_router",
    "stream_api_router",
]
