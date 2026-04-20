"""
backend/schemas/detection.py
Pydantic schemas for Detection model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Base ────────────────────────────────────────────────────────────────────
class DetectionBase(BaseModel):
    plate_text:     str         = Field(..., max_length=20)
    plate_raw:      Optional[str] = None
    confidence:     Optional[float] = Field(None, ge=0.0, le=1.0)
    ocr_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    region:         Optional[str] = None
    region_code:    Optional[str] = None
    vehicle_type:   Optional[str] = None
    source_type:    Optional[str] = "upload"
    status:         Optional[str] = "valid"
    camera_id:      Optional[int] = None


# ─── Create ──────────────────────────────────────────────────────────────────
class DetectionCreate(DetectionBase):
    image_path:  Optional[str] = None
    crop_path:   Optional[str] = None
    raw_frame_ts: Optional[datetime] = None


# ─── Response ────────────────────────────────────────────────────────────────
class DetectionResponse(DetectionBase):
    id:           int
    image_path:   Optional[str] = None
    crop_path:    Optional[str] = None
    detected_at:  datetime
    created_at:   datetime

    # Nested camera info (optional)
    camera_name:  Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Paginated List ───────────────────────────────────────────────────────────
class DetectionListResponse(BaseModel):
    items:      list[DetectionResponse]
    total:      int
    page:       int
    limit:      int
    total_pages: int
