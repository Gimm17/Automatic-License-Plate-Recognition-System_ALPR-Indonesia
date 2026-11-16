import asyncio
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.camera import Camera
from models.detection import Detection
from routers.stats import get_dashboard_stats, get_stats_by_source


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return Session()


def test_stats_payload_contains_current_frontend_fields():
    db = make_db()
    db.add(Camera(name="Gate 1", is_active=True, stream_fps=5))
    db.add_all(
        [
            Detection(
                plate_text="B 1234 XYZ",
                confidence=0.8,
                status="valid",
                source_type="upload",
                detected_at=datetime.utcnow(),
            ),
            Detection(
                plate_text="UNKNOWN",
                confidence=0.0,
                status="ocr_failed",
                source_type="stream",
                detected_at=datetime.utcnow(),
            ),
        ]
    )
    db.commit()

    response = asyncio.run(get_dashboard_stats(days=1, db=db))
    data = response["data"]

    assert "ocr_accuracy_pct" in data
    assert "avg_confidence_pct" in data
    assert data["total_detections"] == 2


def test_stats_by_source_returns_source_breakdown():
    db = make_db()
    db.add(
        Detection(
            plate_text="B 1234 XYZ",
            confidence=0.8,
            status="valid",
            source_type="upload",
            detected_at=datetime.utcnow(),
        )
    )
    db.commit()

    response = asyncio.run(get_stats_by_source(days=7, db=db))

    assert response["data"] == [{"source": "upload", "count": 1}]
