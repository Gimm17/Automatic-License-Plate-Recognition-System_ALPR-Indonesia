"""
backend/routers/stream.py
Fase 2 — WebSocket live CCTV stream endpoint.

Endpoints:
  WS  /ws/stream/{camera_id}       — Live stream with ALPR processing
  GET /api/stream/status            — List active streams
  POST /api/stream/{camera_id}/stop — Signal a stream to stop
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import get_db
from models.camera import Camera
from utils.response import success_response, error_response
from fastapi import Request

logger = logging.getLogger(__name__)

# Two routers: one for WebSocket (/ws), one for REST helpers (/api/stream)
ws_router  = APIRouter(tags=["Stream WebSocket"])
api_router = APIRouter(prefix="/api/stream", tags=["Stream Management"])


# ─── WS /ws/stream/{camera_id} ───────────────────────────────────────────────
@ws_router.websocket("/ws/stream/{camera_id}")
async def websocket_stream(
    websocket: WebSocket,
    camera_id: int,
    request: Request,
    source_override: Optional[str] = None,  # Query param: ?source_override=rtsp://...
):
    """
    WebSocket endpoint for live ALPR stream.

    Path param:
        camera_id: ID of the camera to stream.

    Query params:
        source_override: Optional RTSP URL to override the DB record's rtsp_url.
                         Useful for testing with a local file or webcam (e.g. ?source_override=0).

    WebSocket message format (sent to client):
        {
            "type":        "frame" | "connected" | "error",
            "frame":       "<base64 JPEG>",       # present on type=frame
            "detections":  [...],                  # present on type=frame
            "frame_count": int,
            "fps_display": float,
            "camera_id":   int,
        }

    WebSocket receive (client → server):
        {"action": "stop"}  — Client sends this to gracefully stop the stream.
    """
    stream_service = request.app.state.stream
    db: Session = next(get_db())

    # ── Resolve the RTSP source ────────────────────────────────────────────
    if source_override:
        rtsp_source = source_override
        logger.info(f"Stream override: camera_id={camera_id} source={rtsp_source}")
    else:
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if not camera:
            await websocket.accept()
            await websocket.send_json({
                "type":    "error",
                "message": f"Camera with id={camera_id} not found in database",
            })
            await websocket.close()
            return

        if not camera.rtsp_url:
            await websocket.accept()
            await websocket.send_json({
                "type":    "error",
                "message": f"Camera '{camera.name}' has no RTSP URL configured",
            })
            await websocket.close()
            return

        if not camera.is_active:
            await websocket.accept()
            await websocket.send_json({
                "type":    "error",
                "message": f"Camera '{camera.name}' is currently inactive",
            })
            await websocket.close()
            return

        rtsp_source = camera.rtsp_url

    try:
        await stream_service.start_stream(
            websocket  = websocket,
            camera_id  = camera_id,
            source     = rtsp_source,
            db         = db,
        )
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: camera_id={camera_id}")
    except Exception as e:
        logger.exception(f"Unhandled stream error: camera_id={camera_id} error={e}")
    finally:
        db.close()


# ─── GET /api/stream/status ───────────────────────────────────────────────────
@api_router.get("/status")
async def get_stream_status(request: Request, db: Session = Depends(get_db)):
    """
    Return a list of currently active streams and camera statuses.

    Returns:
        {
            "total_active": int,
            "cameras": [
                {
                    "camera_id":   int,
                    "name":        str,
                    "location":    str,
                    "is_active":   bool,
                    "has_rtsp":    bool,
                    "streaming":   bool,   # True if there's an active WS connection
                }
            ]
        }
    """
    stream_service = request.app.state.stream
    cameras = db.query(Camera).order_by(Camera.id).all()

    camera_list = [
        {
            "camera_id": c.id,
            "name":      c.name,
            "location":  c.location or "",
            "is_active": c.is_active,
            "has_rtsp":  bool(c.rtsp_url),
            "streaming": stream_service.is_streaming(c.id),
        }
        for c in cameras
    ]

    active_count = sum(1 for c in camera_list if c["streaming"])

    return success_response(
        {
            "total_active": active_count,
            "cameras":      camera_list,
        }
    )


# ─── Init package — services/__init__.py helper ───────────────────────────────
def get_routers():
    """Return both routers for inclusion in main.py."""
    return ws_router, api_router
