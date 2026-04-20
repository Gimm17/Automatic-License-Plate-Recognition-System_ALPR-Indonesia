"""
backend/models/detection.py
SQLAlchemy ORM model for the `detections` table.
"""

from datetime import datetime
from sqlalchemy import (
    BigInteger, Column, Enum, Float, ForeignKey,
    Index, String, Text, TIMESTAMP
)
from sqlalchemy.orm import relationship
from database import Base


class Detection(Base):
    __tablename__ = "detections"

    id              = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id       = Column(BigInteger, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    plate_text      = Column(String(20), nullable=False)
    plate_raw       = Column(String(20), nullable=True)      # OCR raw before cleaning
    confidence      = Column(Float, nullable=True)            # YOLOv8 confidence 0‑1
    ocr_confidence  = Column(Float, nullable=True)            # PaddleOCR confidence 0‑1
    region          = Column(String(100), nullable=True)      # e.g. "DKI Jakarta"
    region_code     = Column(String(5), nullable=True)        # e.g. "B"
    vehicle_type    = Column(String(50), nullable=True)
    image_path      = Column(String(255), nullable=True)      # Annotated image path
    crop_path       = Column(String(255), nullable=True)      # Cropped plate path
    source_type     = Column(
        Enum("upload", "stream", "video_batch", name="source_type_enum"),
        nullable=True,
        default="upload",
    )
    status          = Column(
        Enum("valid", "invalid", "watchlist", "ocr_failed", name="detection_status_enum"),
        nullable=False,
        default="valid",
    )
    raw_frame_ts    = Column(TIMESTAMP, nullable=True)        # Timestamp of stream frame
    detected_at     = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    created_at      = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # ─── Relationships ────────────────────────────────────────────────────────
    camera = relationship("Camera", back_populates="detections", lazy="select")

    # ─── Indexes ─────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_plate_text",  "plate_text"),
        Index("idx_detected_at", "detected_at"),
        Index("idx_status",      "status"),
    )

    def __repr__(self) -> str:
        return f"<Detection id={self.id} plate={self.plate_text} status={self.status}>"
