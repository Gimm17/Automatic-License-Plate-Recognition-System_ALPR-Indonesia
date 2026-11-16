import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.detection import Detection
from services.detection_worker import DetectionWorker


class FakeYolo:
    def detect(self, frame):
        return [{"bbox": [0, 0, 20, 20], "confidence": 0.9, "crop": frame[0:20, 0:20]}]


class FakeOcr:
    def read_plate(self, crop):
        return {"text": "B1234XYZ", "confidence": 0.9}


def test_worker_detect_uses_shared_pipeline(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    monkeypatch.setattr("services.detection_worker.SessionLocal", Session)

    worker = DetectionWorker(FakeYolo(), FakeOcr())
    frame = np.zeros((40, 80, 3), dtype=np.uint8)

    detections = worker._detect(camera_id=7, frame=frame)

    assert detections[0]["plate_text"] == "B 1234 XYZ"
    db = Session()
    try:
        record = db.query(Detection).one()
        assert record.camera_id == 7
        assert record.status == "valid"
    finally:
        db.close()
