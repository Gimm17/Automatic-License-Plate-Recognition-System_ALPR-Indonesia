"""
backend/routers/export.py
Fase 2 — Export detections to CSV / JSON.

Endpoints:
  GET /api/export/csv    — Export filtered detections as CSV
  GET /api/export/json   — Export filtered detections as JSON
  GET /api/export/status — Check if an export is available (caching)
"""

import csv
import io
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.detection import Detection
from models.camera import Camera
from utils.response import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["Export"])


# ─── Shared query builder ─────────────────────────────────────────────────────
def _build_query(
    db: Session,
    camera_id:  Optional[int],
    status:     Optional[str],
    date_from:  Optional[str],
    date_to:    Optional[str],
    search:     Optional[str],
    source_type: Optional[str],
):
    """Build filtered query across multiple optional parameters."""
    query = (
        db.query(Detection)
        .outerjoin(Camera, Detection.camera_id == Camera.id)
    )

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
            query = query.filter(
                Detection.detected_at >= datetime.fromisoformat(date_from)
            )
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(
                Detection.detected_at <= datetime.fromisoformat(date_to)
            )
        except ValueError:
            pass

    return query.order_by(Detection.detected_at.desc())


def _row_to_dict(d: Detection) -> dict:
    return {
        "id":            d.id,
        "plate_text":    d.plate_text,
        "plate_raw":     d.plate_raw or "",
        "status":        d.status,
        "confidence":    round((d.confidence or 0) * 100, 1),
        "ocr_confidence": round((d.ocr_confidence or 0) * 100, 1),
        "region":        d.region or "",
        "region_code":   d.region_code or "",
        "vehicle_type":  d.vehicle_type or "",
        "source_type":   d.source_type or "",
        "camera_id":     d.camera_id or "",
        "camera_name":   d.camera.name if d.camera else "",
        "detected_at":   d.detected_at.isoformat() if d.detected_at else "",
    }


# ─── GET /api/export/csv ─────────────────────────────────────────────────────
@router.get("/csv")
async def export_csv(
    camera_id:   Optional[int] = None,
    status:      Optional[str] = None,
    date_from:   Optional[str] = None,
    date_to:     Optional[str] = None,
    search:      Optional[str] = None,
    source_type: Optional[str] = None,
    limit:       int           = 10_000,
    db: Session = Depends(get_db),
):
    """
    Stream detections as a downloadable CSV file.

    Supports all filter params: camera_id, status, date_from, date_to, search, source_type.
    Max rows: 10,000 (use date filters for larger exports).
    """
    query = _build_query(db, camera_id, status, date_from, date_to, search, source_type)
    rows  = query.limit(limit).all()

    if not rows:
        return error_response("No data found matching the given filters", code=404)

    # ── Build CSV in-memory ───────────────────────────────────────────────
    output = io.StringIO()
    fieldnames = [
        "id", "plate_text", "plate_raw", "status",
        "confidence", "ocr_confidence", "region", "region_code",
        "vehicle_type", "source_type", "camera_id", "camera_name", "detected_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for d in rows:
        writer.writerow(_row_to_dict(d))

    output.seek(0)
    timestamp  = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename   = f"alpr_detections_{timestamp}.csv"

    logger.info(f"CSV export: {len(rows)} rows → {filename}")

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── GET /api/export/json ─────────────────────────────────────────────────────
@router.get("/json")
async def export_json(
    camera_id:   Optional[int] = None,
    status:      Optional[str] = None,
    date_from:   Optional[str] = None,
    date_to:     Optional[str] = None,
    search:      Optional[str] = None,
    source_type: Optional[str] = None,
    limit:       int           = 5_000,
    db: Session = Depends(get_db),
):
    """
    Export detections as a downloadable JSON file.

    Supports same filter params as CSV export.
    """
    query = _build_query(db, camera_id, status, date_from, date_to, search, source_type)
    rows  = query.limit(limit).all()

    if not rows:
        return error_response("No data found matching the given filters", code=404)

    data = [_row_to_dict(d) for d in rows]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename  = f"alpr_detections_{timestamp}.json"

    payload = json.dumps(
        {
            "exported_at": datetime.utcnow().isoformat(),
            "total":       len(data),
            "filters": {
                "camera_id":   camera_id,
                "status":      status,
                "date_from":   date_from,
                "date_to":     date_to,
                "search":      search,
                "source_type": source_type,
            },
            "detections": data,
        },
        indent=2,
        ensure_ascii=False,
    )

    logger.info(f"JSON export: {len(rows)} rows → {filename}")

    return StreamingResponse(
        iter([payload]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── GET /api/export/status ───────────────────────────────────────────────────
@router.get("/status")
async def export_status(db: Session = Depends(get_db)):
    """
    Return a quick summary of exportable data size.

    Helps frontend show record count before triggering export.
    """
    total         = db.query(Detection).count()
    today         = datetime.utcnow().strftime("%Y-%m-%d")
    today_count   = (
        db.query(Detection)
        .filter(Detection.detected_at >= datetime.utcnow().replace(hour=0, minute=0, second=0))
        .count()
    )

    return success_response(
        {
            "total_records":      total,
            "today_records":      today_count,
            "max_csv_export":     10_000,
            "max_json_export":    5_000,
            "date":               today,
        }
    )
