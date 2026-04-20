"""
backend/routers/cameras.py
Fase 2 — Camera management endpoints.

Endpoints:
  GET    /api/cameras          — List all cameras
  POST   /api/cameras          — Register a new camera
  GET    /api/cameras/{id}     — Get camera detail
  PUT    /api/cameras/{id}     — Update camera config
  DELETE /api/cameras/{id}     — Deactivate (soft delete) camera
  POST   /api/cameras/{id}/test — Test RTSP connectivity
"""

import logging
from typing import Optional

import cv2
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.camera import Camera
from schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from utils.response import success_response, error_response, paginated_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


# ─── GET /api/cameras ─────────────────────────────────────────────────────────
@router.get("")
async def list_cameras(
    page:      int  = 1,
    limit:     int  = 50,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Return paginated list of cameras.

    Query params:
        page:      Page number (default 1)
        limit:     Items per page (default 50)
        is_active: Filter by active status (optional)
    """
    query = db.query(Camera)
    if is_active is not None:
        query = query.filter(Camera.is_active == is_active)

    total  = query.count()
    offset = (page - 1) * limit
    items  = query.order_by(Camera.created_at.desc()).offset(offset).limit(limit).all()

    serialized = [CameraResponse.model_validate(c).model_dump() for c in items]
    return paginated_response(serialized, total, page, limit)


# ─── POST /api/cameras ────────────────────────────────────────────────────────
@router.post("")
async def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    """
    Register a new camera.

    Body:
        name:       Camera display name (required)
        location:   Physical location description
        rtsp_url:   RTSP stream URL
        is_active:  Whether to activate immediately (default true)
        stream_fps: FPS to process for ALPR (default 5)
    """
    # Check duplicate name
    existing = db.query(Camera).filter(Camera.name == payload.name).first()
    if existing:
        return error_response(
            f"Camera with name '{payload.name}' already exists", code=409
        )

    camera = Camera(**payload.model_dump())
    db.add(camera)
    db.commit()
    db.refresh(camera)

    logger.info(f"Camera created: id={camera.id} name={camera.name}")
    return success_response(
        CameraResponse.model_validate(camera).model_dump(),
        "Camera registered successfully",
    )


# ─── GET /api/cameras/{id} ────────────────────────────────────────────────────
@router.get("/{camera_id}")
async def get_camera(camera_id: int, db: Session = Depends(get_db)):
    """Return details for a single camera by ID."""
    camera = _get_or_404(camera_id, db)
    return success_response(CameraResponse.model_validate(camera).model_dump())


# ─── PUT /api/cameras/{id} ────────────────────────────────────────────────────
@router.put("/{camera_id}")
async def update_camera(
    camera_id: int,
    payload: CameraUpdate,
    db: Session = Depends(get_db),
):
    """
    Update camera configuration.

    Only provided (non-None) fields are updated.
    """
    camera = _get_or_404(camera_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    db.commit()
    db.refresh(camera)

    logger.info(f"Camera updated: id={camera_id} fields={list(update_data.keys())}")
    return success_response(
        CameraResponse.model_validate(camera).model_dump(),
        "Camera updated successfully",
    )


# ─── DELETE /api/cameras/{id} ────────────────────────────────────────────────
@router.delete("/{camera_id}")
async def deactivate_camera(camera_id: int, db: Session = Depends(get_db)):
    """
    Soft-delete: sets is_active=False instead of removing the record.
    Detection history is preserved.
    """
    camera = _get_or_404(camera_id, db)
    camera.is_active = False
    db.commit()

    logger.info(f"Camera deactivated: id={camera_id}")
    return success_response(None, f"Camera '{camera.name}' deactivated")


# ─── POST /api/cameras/{id}/test ─────────────────────────────────────────────
@router.post("/{camera_id}/test")
async def test_camera_connection(camera_id: int, db: Session = Depends(get_db)):
    """
    Test RTSP connectivity for a camera.

    Attempts to open the stream with OpenCV and read one frame.
    Returns latency and frame resolution if successful.
    """
    camera = _get_or_404(camera_id, db)

    if not camera.rtsp_url:
        return error_response("No RTSP URL configured for this camera", code=400)

    import time
    start = time.time()

    try:
        cap = cv2.VideoCapture(camera.rtsp_url)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5s timeout
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)

        if not cap.isOpened():
            return error_response(
                "Cannot connect to RTSP stream. Check URL and network.", code=503
            )

        ret, frame = cap.read()
        cap.release()
        elapsed_ms = int((time.time() - start) * 1000)

        if not ret or frame is None:
            return error_response("Connected but cannot read frames", code=503)

        h, w = frame.shape[:2]
        return success_response(
            {
                "camera_id":    camera_id,
                "reachable":    True,
                "latency_ms":   elapsed_ms,
                "resolution":   f"{w}x{h}",
                "rtsp_url":     camera.rtsp_url,
            },
            "Camera is reachable",
        )

    except Exception as e:
        logger.warning(f"Camera test failed for id={camera_id}: {e}")
        return error_response(f"Connection test failed: {str(e)}", code=503)


# ─── Helper ───────────────────────────────────────────────────────────────────
def _get_or_404(camera_id: int, db: Session) -> Camera:
    """Fetch camera by ID or return a 404 error response."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera
