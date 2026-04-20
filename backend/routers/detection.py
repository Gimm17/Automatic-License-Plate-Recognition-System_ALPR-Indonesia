"""
backend/routers/detection.py
Fase 1 — Core detection router.

Endpoints:
  POST /api/detect        — Upload image/video and run ALPR pipeline
  GET  /api/detections    — Paginated detection history with filters
  GET  /api/detections/{id} — Single detection detail
"""

import uuid
import logging
from pathlib import Path
from typing import Optional

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.detection import Detection
from schemas.detection import DetectionResponse, DetectionListResponse
from services.plate_validator import validate_plate
from utils.image_utils import save_image, resize_for_display
from utils.response import success_response, error_response, paginated_response

# ML services injected at startup from main.py (see app.state)
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Detection"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/bmp", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo"}


# ─── POST /api/detect ─────────────────────────────────────────────────────────
@router.post("/detect")
async def detect_plate(
    request: Request,
    file: UploadFile = File(...),
    camera_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload an image or video file and run the full ALPR pipeline.

    Returns:
        {
            "detections": [...],
            "annotated_image_url": str | null,
            "total_found": int,
        }
    """
    yolo = request.app.state.yolo
    ocr  = request.app.state.ocr

    content_type = (file.content_type or "").lower()
    is_image = content_type in ALLOWED_IMAGE_TYPES
    is_video = content_type in ALLOWED_VIDEO_TYPES

    if not is_image and not is_video:
        return error_response(
            f"Unsupported file type: {content_type}. "
            "Allowed: JPEG, PNG, BMP, WEBP, MP4, AVI, MOV",
            code=422,
        )

    # ── Save upload to temp ────────────────────────────────────────────────
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "upload").suffix or ".jpg"
    temp_filename = f"{uuid.uuid4().hex}{ext}"
    temp_path = settings.temp_dir / temp_filename

    try:
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            return error_response(
                f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB", code=413
            )
        temp_path.write_bytes(contents)
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        return error_response("Failed to save uploaded file", code=500)

    # ── Run pipeline ────────────────────────────────────────────────────────
    try:
        if is_image:
            results = await _process_image(
                temp_path, camera_id, yolo, ocr, db
            )
        else:
            results = await _process_video(
                temp_path, camera_id, yolo, ocr, db
            )
        return success_response(results, "Detection completed")
    except Exception as e:
        logger.exception(f"Detection pipeline error: {e}")
        return error_response(f"Detection failed: {str(e)}", code=500)
    finally:
        # Clean up temp file
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass


async def _process_image(
    image_path: Path,
    camera_id: Optional[int],
    yolo,
    ocr,
    db: Session,
) -> dict:
    """Run YOLO → crop → OCR → validate → save → annotate for a single image."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError("Cannot read image file")

    raw_detections = yolo.detect(img)
    enriched: list[dict] = []

    for det in raw_detections:
        crop    = det["crop"]
        bbox    = det["bbox"]
        conf    = det["confidence"]

        # OCR
        ocr_result = ocr.read_plate(crop)
        plate_text = ocr_result.get("text", "")
        ocr_conf   = ocr_result.get("confidence", 0.0)

        # Validate + enrich
        validation = validate_plate(plate_text) if plate_text else {
            "plate": "", "plate_raw": "", "valid": False,
            "status": "ocr_failed", "region": "", "region_code": "",
        }

        status = validation["status"]
        if not plate_text:
            status = "ocr_failed"

        # Save crop
        crop_path_obj = save_image(
            crop, settings.results_dir / "crops",
            f"{uuid.uuid4().hex}_crop.jpg",
        )

        # Build detection dict with plate_text for annotator
        det["plate_text"] = validation["plate"]
        det["ocr_confidence"] = ocr_conf

        # Save to DB
        db_record = Detection(
            camera_id      = camera_id,
            plate_text     = validation["plate"] or plate_text or "UNKNOWN",
            plate_raw      = plate_text,
            confidence     = conf,
            ocr_confidence = ocr_conf,
            region         = validation.get("region", ""),
            region_code    = validation.get("region_code", ""),
            source_type    = "upload",
            status         = status,
            crop_path      = str(crop_path_obj.relative_to(
                settings.storage_dir
            )) if crop_path_obj else None,
        )
        db.add(db_record)

        enriched.append({
            "bbox":          bbox,
            "confidence":    conf,
            "plate_text":    validation["plate"],
            "plate_raw":     plate_text,
            "ocr_confidence": ocr_conf,
            "region":        validation.get("region", ""),
            "region_code":   validation.get("region_code", ""),
            "status":        status,
            "valid":         validation.get("valid", False),
            "crop_url":      f"/storage/crops/{crop_path_obj.name}" if crop_path_obj else None,
        })

    # Annotate full image
    annotated = yolo.annotate(img, raw_detections)
    annotated_resized = resize_for_display(annotated, max_width=1200)
    annotated_path = save_image(
        annotated_resized, settings.results_dir,
        f"{uuid.uuid4().hex}_annotated.jpg",
    )

    # Update DB records with annotated_image_path and commit
    for record in db.new:
        if isinstance(record, Detection) and not record.image_path:
            record.image_path = str(
                annotated_path.relative_to(settings.storage_dir)
            )
    db.commit()

    return {
        "detections":          enriched,
        "annotated_image_url": f"/storage/{annotated_path.relative_to(settings.storage_dir).as_posix()}",
        "total_found":         len(enriched),
    }


async def _process_video(
    video_path: Path,
    camera_id: Optional[int],
    yolo,
    ocr,
    db: Session,
    frame_interval: int = 30,
) -> dict:
    """Extract frames from video and run ALPR on each sampled frame."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError("Cannot open video file")

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

            raw = yolo.detect(frame)
            for det in raw:
                ocr_result = ocr.read_plate(det["crop"])
                plate_text = ocr_result.get("text", "")
                ocr_conf   = ocr_result.get("confidence", 0.0)

                validation = validate_plate(plate_text) if plate_text else {
                    "plate": "", "valid": False,
                    "status": "ocr_failed", "region": "", "region_code": "",
                }

                status = validation["status"] if plate_text else "ocr_failed"

                db_record = Detection(
                    camera_id      = camera_id,
                    plate_text     = validation.get("plate") or "UNKNOWN",
                    plate_raw      = plate_text,
                    confidence     = det["confidence"],
                    ocr_confidence = ocr_conf,
                    region         = validation.get("region", ""),
                    region_code    = validation.get("region_code", ""),
                    source_type    = "video_batch",
                    status         = status,
                )
                db.add(db_record)

                all_detections.append({
                    "plate_text":    validation.get("plate", ""),
                    "confidence":    det["confidence"],
                    "ocr_confidence": ocr_conf,
                    "status":        status,
                    "frame":         frame_count,
                })
    finally:
        cap.release()

    db.commit()

    unique_plates = list({d["plate_text"] for d in all_detections if d["plate_text"]})
    return {
        "detections":   all_detections,
        "total_found":  len(all_detections),
        "unique_plates": unique_plates,
        "frames_processed": frame_count // frame_interval,
        "annotated_image_url": None,
    }


# ─── GET /api/detections ──────────────────────────────────────────────────────
@router.get("/detections")
async def list_detections(
    page:      int = 1,
    limit:     int = 20,
    camera_id: Optional[int] = None,
    status:    Optional[str] = None,
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    search:    Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Paginated list of detections with optional filters."""
    from datetime import datetime
    from sqlalchemy import or_

    query = db.query(Detection)

    if camera_id:
        query = query.filter(Detection.camera_id == camera_id)
    if status:
        query = query.filter(Detection.status == status)
    if search:
        query = query.filter(
            or_(
                Detection.plate_text.ilike(f"%{search}%"),
                Detection.region.ilike(f"%{search}%"),
            )
        )
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.filter(Detection.detected_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.filter(Detection.detected_at <= dt_to)
        except ValueError:
            pass

    total  = query.count()
    offset = (page - 1) * limit
    items  = (
        query.order_by(Detection.detected_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    serialized = []
    for item in items:
        d = DetectionResponse.model_validate(item).model_dump()
        if item.camera:
            d["camera_name"] = item.camera.name
        serialized.append(d)

    return paginated_response(serialized, total, page, limit)


# ─── GET /api/detections/{id} ────────────────────────────────────────────────
@router.get("/detections/{detection_id}")
async def get_detection(detection_id: int, db: Session = Depends(get_db)):
    """Return a single detection by ID."""
    record = db.query(Detection).filter(Detection.id == detection_id).first()
    if not record:
        return error_response("Detection not found", code=404)

    d = DetectionResponse.model_validate(record).model_dump()
    if record.camera:
        d["camera_name"] = record.camera.name
    return success_response(d)
