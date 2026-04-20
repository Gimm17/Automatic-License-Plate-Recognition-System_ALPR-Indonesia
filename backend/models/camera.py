"""
backend/models/camera.py
SQLAlchemy ORM model for the `cameras` table.
"""

from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    name        = Column(String(100), nullable=False)
    location    = Column(String(200), nullable=True)
    rtsp_url    = Column(Text, nullable=True)          # RTSP URL (should be encrypted in prod)
    is_active   = Column(Boolean, nullable=False, default=True)
    stream_fps  = Column(Integer, nullable=False, default=5)
    created_at  = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # ─── Relationships ────────────────────────────────────────────────────────
    detections = relationship(
        "Detection",
        back_populates="camera",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Camera id={self.id} name={self.name} active={self.is_active}>"
