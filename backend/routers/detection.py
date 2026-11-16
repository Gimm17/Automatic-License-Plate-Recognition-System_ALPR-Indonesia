"""
backend/routers/detection.py
Upload detection and detection history endpoints.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.detection import Detection
from services.alpr_pipeline import (
    apply_image_path,
    process_frame,
    relative_to_storage,
    serialize_detection,
    storage_url,
)
from utils.image_utils import resize_for_display, save_image
from utils.response import error_response, paginated_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Detection"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/bmp", "image/webp"}
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/avi",
    "video/quicktime",
    "video/x-msvideo",
    "application/mp4",
}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov"}


@router.post("/detect")
async def detect_plate(
    request: Request,
    file: UploadFile = File(...),
    camera_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload an image or video file and run the ALPR pipeline."""
    yolo = getattr(request.app.state, "yolo", None)
    ocr = getattr(request.app.state, "ocr", None)
    if yolo is None or ocr is None or not ocr.is_available():
        return error_response(
            "Detection service unavailable. YOLO or OCR is not loaded.",
            code=503,
        )

    content_type = (file.content_type or "").lower().split(";")[0]
    ext = Path(file.filename or "upload").suffix.lower()
    is_image, is_video = classify_upload_media(content_type, ext)
    if not is_image and not is_video:
        return error_response(
            f"Unsupported file type: {content_type or ext or 'unknown'}. Allowed: JPEG, PNG, BMP, WEBP, MP4, AVI, MOV",
            code=422,
        )

    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    ext = ext or ".jpg"
    temp_path = settings.temp_dir / f"{uuid.uuid4().hex}{ext}"

    try:
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            return error_response(f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB", code=413)
        temp_path.write_bytes(contents)

        if is_image:
            result = await _process_image(temp_path, camera_id, yolo, ocr, db)
        else:
            result = await _process_video(temp_path, camera_id, yolo, ocr, db)
        return success_response(result, "Detection completed")
    except Exception as exc:
        logger.exception("Detection pipeline error: %s", exc)
        db.rollback()
        return error_response(f"Detection failed: {exc}", code=500)
    finally:
        temp_path.unlink(missing_ok=True)

def classify_upload_media(content_type: str, ext: str) -> tuple[bool, bool]:
    """Classify upload by MIME type, with extension fallback for generic browser uploads."""
    if content_type in ALLOWED_IMAGE_TYPES:
        return True, False
    if content_type in ALLOWED_VIDEO_TYPES:
        return False, True
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return True, False
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return False, True
    return False, False


async def _process_image(
    image_path: Path,
    camera_id: Optional[int],
    yolo,
    ocr,
    db: Session,
) -> dict:
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError("Cannot read image file")

    pipeline_result = process_frame(
        img,
        yolo=yolo,
        ocr=ocr,
        db=db,
        camera_id=camera_id,
        source_type="upload",
        save_crops=True,
        persist=True,
    )

    annotated = yolo.annotate(img, pipeline_result["raw_detections"])
    annotated_resized = resize_for_display(annotated, max_width=1200)
    annotated_path = save_image(
        annotated_resized,
        settings.results_dir,
        f"{uuid.uuid4().hex}_annotated.jpg",
    )
    apply_image_path(pipeline_result["records"], annotated_path)
    db.commit()

    annotated_rel = relative_to_storage(annotated_path)
    return {
        "detections": pipeline_result["detections"],
        "annotated_image_url": storage_url(annotated_rel),
        "image_width": pipeline_result["image_width"],
        "image_height": pipeline_result["image_height"],
        "total_found": len(pipeline_result["detections"]),
    }


async def _process_video(
    video_path: Path,
    camera_id: Optional[int],
    yolo,
    ocr,
    db: Session,
    frame_interval: int = 30,
) -> dict:
    # Resolve to absolute path for reliable OpenCV access on all platforms
    abs_path = str(video_path.resolve())
    file_size = video_path.stat().st_size if video_path.exists() else 0
    logger.info("Opening video: %s (%d bytes)", abs_path, file_size)

    if file_size == 0:
        raise ValueError("Video file is empty (0 bytes): " + abs_path)

    cap = cv2.VideoCapture(abs_path)
    if not cap.isOpened():
        raise ValueError(
            "Cannot open video file (OpenCV VideoCapture failed). "
            "Path: " + abs_path + ", Size: " + str(file_size) + " bytes. "
            "Ensure the video codec is supported (H.264/H.265 MP4, AVI, MOV)."
        )

    all_detections: list[dict] = []
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % frame_interval != 0:
                continue

            pipeline_result = process_frame(
                frame,
                yolo=yolo,
                ocr=ocr,
                db=db,
                camera_id=camera_id,
                source_type="video_batch",
                save_crops=False,
                persist=True,
            )
            for item in pipeline_result["detections"]:
                all_detections.append({**item, "frame": frame_count})
    finally:
        cap.release()

    db.commit()
    unique_plates = sorted({d["plate_text"] for d in all_detections if d.get("plate_text")})
    return {
        "detections": all_detections,
        "total_found": len(all_detections),
        "unique_plates": unique_plates,
        "frames_processed": frame_count // frame_interval,
        "annotated_image_url": None,
        "image_width": None,
        "image_height": None,
    }


@router.get("/detections")
async def list_detections(
    page: int = 1,
    limit: int = 20,
    camera_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    source_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Paginated detection history with optional filters."""
    query = db.query(Detection)

    if camera_id:
        query = query.filter(Detection.camera_id == camera_id)
    if status:
        query = query.filter(Detection.status == status)
    if source_type:
        query = query.filter(Detection.source_type == source_type)
    if search:
        query = query.filter(
            or_(
                Detection.plate_text.ilike(f"%{search}%"),
                Detection.region.ilike(f"%{search}%"),
            )
        )
    if date_from:
        try:
            query = query.filter(Detection.detected_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Detection.detected_at <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    total = query.count()
    page = max(1, page)
    limit = max(1, min(limit, 100))
    items = (
        query.order_by(Detection.detected_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return paginated_response([serialize_detection(item) for item in items], total, page, limit)


@router.get("/detections/{detection_id}")
async def get_detection(detection_id: int, db: Session = Depends(get_db)):
    """Return a single detection by ID."""
    record = db.query(Detection).filter(Detection.id == detection_id).first()
    if not record:
        return error_response("Detection not found", code=404)
    return success_response(serialize_detection(record))
