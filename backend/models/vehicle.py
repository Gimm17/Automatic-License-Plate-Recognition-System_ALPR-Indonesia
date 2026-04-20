"""
backend/models/vehicle.py
SQLAlchemy ORM model for the `vehicles` lookup table.
"""

from datetime import datetime
from sqlalchemy import BigInteger, Column, Enum, Index, Integer, String, Text, TIMESTAMP
from database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id           = Column(BigInteger, primary_key=True, autoincrement=True)
    plate_text   = Column(String(20), unique=True, nullable=False)
    owner_name   = Column(String(100), nullable=True)
    vehicle_type = Column(String(50), nullable=True)
    brand        = Column(String(50), nullable=True)
    color        = Column(String(30), nullable=True)
    year         = Column(Integer, nullable=True)
    status       = Column(
        Enum("normal", "watchlist", "stolen", "expired", name="vehicle_status_enum"),
        nullable=False,
        default="normal",
    )
    notes        = Column(Text, nullable=True)
    created_at   = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # ─── Indexes ─────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_vehicle_plate", "plate_text"),
        Index("idx_vehicle_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Vehicle plate={self.plate_text} status={self.status}>"
