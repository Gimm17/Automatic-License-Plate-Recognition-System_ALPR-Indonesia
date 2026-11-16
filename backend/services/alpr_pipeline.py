"""
backend/services/alpr_pipeline.py
Shared ALPR pipeline used by upload, live stream, and background worker.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from config import settings
from models.detection import Detection
from models.vehicle import Vehicle
from services.plate_validator import clean_ocr_text, validate_plate
from utils.image_utils import crop_region, save_image


def storage_url(relative_path: Optional[str]) -> Optional[str]:
    if not relative_path:
        return None
    return "/storage/" + str(relative_path).replace("\\", "/").lstrip("/")


def relative_to_storage(path: Optional[Path]) -> Optional[str]:
    if not path:
        return None
    return path.relative_to(settings.storage_dir).as_posix()


def bbox_norm(bbox: list[int], image_width: int, image_height: int) -> list[float]:
    if image_width <= 0 or image_height <= 0:
        return [0.0, 0.0, 0.0, 0.0]

    x1, y1, x2, y2 = [float(v) for v in bbox]
    values = [
        x1 / image_width,
        y1 / image_height,
        x2 / image_width,
        y2 / image_height,
    ]
    return [round(min(1.0, max(0.0, v)), 6) for v in values]


def serialize_detection(record: Detection) -> dict:
    data = {
        "id": record.id,
        "camera_id": record.camera_id,
        "plate_text": record.plate_text,
        "plate_raw": record.plate_raw,
        "confidence": record.confidence,
        "ocr_confidence": record.ocr_confidence,
        "region": record.region,
        "region_code": record.region_code,
        "vehicle_type": record.vehicle_type,
        "source_type": record.source_type,
        "status": record.status,
        "image_path": record.image_path,
        "crop_path": record.crop_path,
        "image_url": storage_url(record.image_path),
        "crop_url": storage_url(record.crop_path),
        "camera_name": record.camera.name if record.camera else None,
        "detected_at": record.detected_at.isoformat() if record.detected_at else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
    return data


def apply_image_path(records: list[Detection], image_path: Optional[Path]) -> None:
    rel = relative_to_storage(image_path)
    if not rel:
        return
    for record in records:
        record.image_path = rel


def process_frame(
    frame: np.ndarray,
    *,
    yolo,
    ocr,
    db: Session,
    camera_id: Optional[int] = None,
    source_type: str = "upload",
    save_crops: bool = True,
    raw_frame_ts: Optional[datetime] = None,
    persist: bool = True,
) -> dict:
    """
    Run YOLO -> crop -> OCR -> plate validation -> vehicle lookup -> persistence.
    Returns response-ready detections plus ORM records and raw YOLO detections.
    """
    if frame is None or frame.size == 0:
        raise ValueError("Frame is empty")

    image_height, image_width = frame.shape[:2]
    raw_detections = yolo.detect(frame)
    detections: list[dict] = []
    records: list[Detection] = []

    for det in raw_detections:
        bbox = [int(v) for v in det.get("bbox", [0, 0, 0, 0])]
        crop = det.get("crop")
        if crop is None or getattr(crop, "size", 0) == 0:
            crop = crop_region(frame, bbox)
        if crop is None or getattr(crop, "size", 0) == 0:
            continue

        confidence = float(det.get("confidence", 0.0) or 0.0)
        ocr_result = ocr.read_plate(crop)
        plate_raw = (ocr_result.get("text") or "").strip()
        ocr_confidence = float(ocr_result.get("confidence", 0.0) or 0.0)

        if plate_raw:
            validation = validate_plate(plate_raw)
            status = validation.get("status", "invalid")
        else:
            validation = {
                "plate": "",
                "plate_raw": "",
                "valid": False,
                "status": "ocr_failed",
                "region": "",
                "region_code": "",
            }
            status = "ocr_failed"

        plate_text = validation.get("plate") or clean_ocr_text(plate_raw) or "UNKNOWN"
        vehicle = (
            db.query(Vehicle)
            .filter(Vehicle.plate_text == plate_text)
            .first()
            if plate_text != "UNKNOWN"
            else None
        )

        vehicle_status = None
        vehicle_type = None
        if vehicle:
            vehicle_status = vehicle.status
            vehicle_type = vehicle.vehicle_type
            if vehicle.status != "normal":
                status = "watchlist"

        crop_path_obj = None
        crop_rel = None
        if save_crops:
            crop_path_obj = save_image(
                crop,
                settings.results_dir / "crops",
                f"{uuid.uuid4().hex}_crop.jpg",
            )
            crop_rel = relative_to_storage(crop_path_obj)

        record = Detection(
            camera_id=camera_id,
            plate_text=plate_text,
            plate_raw=plate_raw or None,
            confidence=confidence,
            ocr_confidence=ocr_confidence,
            region=validation.get("region", ""),
            region_code=validation.get("region_code", ""),
            vehicle_type=vehicle_type,
            crop_path=crop_rel,
            source_type=source_type,
            status=status,
            raw_frame_ts=raw_frame_ts,
            detected_at=raw_frame_ts or datetime.utcnow(),
        )
        if persist:
            db.add(record)
            records.append(record)

        det["plate_text"] = plate_text
        det["ocr_confidence"] = ocr_confidence

        detections.append(
            {
                "detection_id": None,
                "bbox": bbox,
                "bbox_norm": bbox_norm(bbox, image_width, image_height),
                "confidence": round(confidence, 4),
                "plate_text": plate_text,
                "plate_raw": plate_raw,
                "ocr_confidence": round(ocr_confidence, 4),
                "region": validation.get("region", ""),
                "region_code": validation.get("region_code", ""),
                "vehicle_type": vehicle_type,
                "vehicle_status": vehicle_status,
                "status": status,
                "valid": bool(validation.get("valid", False)),
                "crop_url": storage_url(crop_rel),
                "camera_id": camera_id,
            }
        )

    if persist and records:
        db.flush()
        for item, record in zip(detections, records):
            item["detection_id"] = record.id

    return {
        "detections": detections,
        "records": records,
        "raw_detections": raw_detections,
        "image_width": image_width,
        "image_height": image_height,
    }
