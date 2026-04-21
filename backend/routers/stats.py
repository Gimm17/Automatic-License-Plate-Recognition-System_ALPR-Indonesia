"""
backend/routers/stats.py
Fase 2 — Dashboard statistics endpoints.

Endpoints:
  GET /api/stats              — Main dashboard summary
  GET /api/stats/chart        — Daily detection counts for chart
  GET /api/stats/by-region    — Breakdown by region code
  GET /api/stats/by-camera    — Detection count per camera
  GET /api/stats/by-source    — Breakdown by source type (upload/stream/video_batch)
  GET /api/stats/alerts       — Active alerts summary (watchlist hits)
"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, and_, case
from sqlalchemy.orm import Session

from database import get_db
from models.detection import Detection
from models.camera import Camera
from models.vehicle import Vehicle
from utils.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stats", tags=["Statistics"])


# ─── GET /api/stats ───────────────────────────────────────────────────────────
@router.get("")
async def get_dashboard_stats(
    days: int = 1,
    db: Session = Depends(get_db),
):
    """
    Main dashboard statistics summary.

    Query params:
        days: Look-back period in days (default 1 = today only)

    Returns:
        {
            "total_detections":   int,
            "valid_detections":   int,
            "invalid_detections": int,
            "ocr_failed":         int,
            "watchlist_hits":     int,
            "ocr_accuracy_pct":   float,
            "avg_confidence_pct": float,
            "active_cameras":     int,
            "total_cameras":      int,
            "period_days":        int,
        }
    """
    since = datetime.utcnow() - timedelta(days=days)

    base_query = db.query(Detection).filter(Detection.detected_at >= since)

    total     = base_query.count()
    valid     = base_query.filter(Detection.status == "valid").count()
    invalid   = base_query.filter(Detection.status == "invalid").count()
    ocr_fail  = base_query.filter(Detection.status == "ocr_failed").count()
    watchlist = base_query.filter(Detection.status == "watchlist").count()

    # OCR accuracy = valid / (total - ocr_failed) * 100
    denominator = total - ocr_fail
    ocr_accuracy = round((valid / denominator * 100), 1) if denominator > 0 else 0.0

    # Average YOLO confidence
    avg_conf_row = (
        base_query.with_entities(func.avg(Detection.confidence)).scalar()
    )
    avg_conf = round((avg_conf_row or 0.0) * 100, 1)

    # Camera counts
    active_cameras = db.query(Camera).filter(Camera.is_active == True).count()
    total_cameras  = db.query(Camera).count()

    # Yesterday comparison
    since_yesterday = since - timedelta(days=days)
    yesterday_total = (
        db.query(Detection)
        .filter(
            Detection.detected_at >= since_yesterday,
            Detection.detected_at < since,
        )
        .count()
    )
    change_vs_yesterday = total - yesterday_total

    return success_response(
        {
            "total_detections":    total,
            "valid_detections":    valid,
            "invalid_detections":  invalid,
            "ocr_failed":          ocr_fail,
            "watchlist_hits":      watchlist,
            "ocr_accuracy_pct":    ocr_accuracy,
            "avg_confidence_pct":  avg_conf,
            "active_cameras":      active_cameras,
            "total_cameras":       total_cameras,
            "period_days":         days,
            "change_vs_prev":      change_vs_yesterday,
        }
    )


# ─── GET /api/stats/chart ─────────────────────────────────────────────────────
@router.get("/chart")
async def get_chart_data(
    days: int = 7,
    db: Session = Depends(get_db),
):
    """
    Daily detection counts for the last N days (for chart rendering).

    Returns:
        [
            {"date": "2024-01-01", "total": 1200, "valid": 1100, "watchlist": 5},
            ...
        ]
    """
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(Detection.detected_at).label("day"),
            func.count(Detection.id).label("total"),
            func.sum(
                case((Detection.status == "valid", 1), else_=0)
            ).label("valid"),
            func.sum(
                case((Detection.status == "watchlist", 1), else_=0)
            ).label("watchlist"),
        )
        .filter(Detection.detected_at >= since)
        .group_by(func.date(Detection.detected_at))
        .order_by(func.date(Detection.detected_at).asc())
        .all()
    )

    chart = [
        {
            "date":      str(row.day),
            "total":     row.total,
            "valid":     int(row.valid or 0),
            "watchlist": int(row.watchlist or 0),
        }
        for row in rows
    ]

    # Fill missing days with zeros so frontend chart is continuous
    chart_map = {item["date"]: item for item in chart}
    filled: list[dict] = []
    for i in range(days):
        day_str = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        filled.append(
            chart_map.get(day_str, {"date": day_str, "total": 0, "valid": 0, "watchlist": 0})
        )

    return success_response(filled)


# ─── GET /api/stats/by-region ─────────────────────────────────────────────────
@router.get("/by-region")
async def get_stats_by_region(
    days: int = 7,
    top_n: int = 10,
    db: Session = Depends(get_db),
):
    """
    Detection count breakdown by region code.

    Returns top N regions sorted by count.
    """
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            Detection.region_code.label("code"),
            Detection.region.label("region"),
            func.count(Detection.id).label("count"),
        )
        .filter(
            Detection.detected_at >= since,
            Detection.region_code.isnot(None),
            Detection.region_code != "",
        )
        .group_by(Detection.region_code, Detection.region)
        .order_by(func.count(Detection.id).desc())
        .limit(top_n)
        .all()
    )

    data = [
        {
            "region_code": row.code,
            "region":      row.region or row.code,
            "count":       row.count,
        }
        for row in rows
    ]
    return success_response(data)


# ─── GET /api/stats/by-camera ─────────────────────────────────────────────────
@router.get("/by-camera")
async def get_stats_by_camera(
    days: int = 1,
    db: Session = Depends(get_db),
):
    """Detection count per camera for the past N days."""
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            Detection.camera_id.label("camera_id"),
            Camera.name.label("camera_name"),
            Camera.location.label("location"),
            func.count(Detection.id).label("count"),
        )
        .outerjoin(Camera, Detection.camera_id == Camera.id)
        .filter(Detection.detected_at >= since)
        .group_by(Detection.camera_id, Camera.name, Camera.location)
        .order_by(func.count(Detection.id).desc())
        .all()
    )

    data = [
        {
            "camera_id":   row.camera_id,
            "camera_name": row.camera_name or f"Camera #{row.camera_id}",
            "location":    row.location or "Unknown",
            "count":       row.count,
        }
        for row in rows
    ]
    return success_response(data)


# ─── GET /api/stats/by-source ─────────────────────────────────────────────────
@router.get("/by-source")
async def get_stats_by_source(
    days: int = 7,
    db: Session = Depends(get_db),
):
    """Breakdown by source type: upload / stream / video_batch."""
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            Detection.source_type.label("source"),
            func.count(Detection.id).label("count"),
        )
        .filter(Detection.detected_at >= since)
        .group_by(Detection.source_type)
        .all()
    )

    data = [{"source": row.source or "unknown", "count": row.count} for row in rows]
    return success_response(data)


# ─── GET /api/stats/alerts ────────────────────────────────────────────────────
@router.get("/alerts")
async def get_alerts_summary(
    hours: int = 24,
    db: Session = Depends(get_db),
):
    """
    Active alert summary: recent watchlist/flagged vehicle detections.

    Returns the last N hours of watchlist hits.
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    rows = (
        db.query(Detection)
        .filter(
            Detection.detected_at >= since,
            Detection.status == "watchlist",
        )
        .order_by(Detection.detected_at.desc())
        .limit(50)
        .all()
    )

    alerts = [
        {
            "id":          r.id,
            "plate_text":  r.plate_text,
            "region":      r.region,
            "camera_id":   r.camera_id,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            "confidence":  r.confidence,
        }
        for r in rows
    ]

    return success_response(
        {
            "total_alerts": len(alerts),
            "period_hours": hours,
            "alerts":       alerts,
        }
    )
