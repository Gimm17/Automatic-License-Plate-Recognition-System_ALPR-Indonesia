import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.detection import Detection
from models.vehicle import Vehicle
from services.alpr_pipeline import process_frame


class FakeYolo:
    def detect(self, frame):
        return [
            {
                "bbox": [10, 20, 60, 70],
                "confidence": 0.91,
                "crop": frame[20:70, 10:60],
            }
        ]


class FakeOcr:
    def __init__(self, text="B1234XYZ", confidence=0.88):
        self.text = text
        self.confidence = confidence

    def read_plate(self, crop):
        return {"text": self.text, "confidence": self.confidence}


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    return db


def test_pipeline_marks_non_normal_vehicle_as_watchlist():
    db = make_db()
    db.add(Vehicle(plate_text="B 1234 XYZ", status="stolen", vehicle_type="SUV"))
    db.commit()

    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    result = process_frame(
        frame,
        yolo=FakeYolo(),
        ocr=FakeOcr(),
        db=db,
        camera_id=1,
        source_type="upload",
        save_crops=False,
    )

    item = result["detections"][0]
    assert item["plate_text"] == "B 1234 XYZ"
    assert item["status"] == "watchlist"
    assert item["vehicle_type"] == "SUV"
    assert item["bbox"] == [10, 20, 60, 70]
    assert item["bbox_norm"] == [0.05, 0.2, 0.3, 0.7]

    record = db.query(Detection).one()
    assert record.status == "watchlist"
    assert record.vehicle_type == "SUV"


def test_pipeline_persists_ocr_failed_detection():
    db = make_db()
    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    result = process_frame(
        frame,
        yolo=FakeYolo(),
        ocr=FakeOcr(text="", confidence=0.0),
        db=db,
        source_type="stream",
        save_crops=False,
    )

    item = result["detections"][0]
    assert item["plate_text"] == "UNKNOWN"
    assert item["status"] == "ocr_failed"
    assert db.query(Detection).one().status == "ocr_failed"
