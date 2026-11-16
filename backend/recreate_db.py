"""
Script: recreate_db.py
Force drop and recreate all tables with correct INTEGER PKs for SQLite.
"""
import sys
sys.path.insert(0, '.')

# Force fresh imports
from database import Base, engine
from models.camera import Camera
from models.vehicle import Vehicle
from models.detection import Detection
import sqlite3

# Check column type
cam_id = Camera.__table__.c['id']
print(f"Camera.id type in SQLAlchemy: {cam_id.type.__class__.__name__}")

# Drop + recreate
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Tables recreated.")

# Check SQLite DDL
db_url = str(engine.url).replace('sqlite:///', '')
conn = sqlite3.connect(db_url)
row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='cameras'").fetchone()
print("DDL:", row[0] if row else "NOT FOUND")

# Test raw insert via SQLAlchemy ORM
from database import SessionLocal
db = SessionLocal()
try:
    cam = Camera(name='Test IPVM ALPR', rtsp_url='rtsp://demo:demo@ipvmdemo.dyndns.org:5541/stream', is_active=True, stream_fps=5)
    db.add(cam)
    db.commit()
    db.refresh(cam)
    print(f"INSERT OK: id={cam.id}, name={cam.name}")
    db.delete(cam)
    db.commit()
    print("Cleanup OK.")
except Exception as e:
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

conn.close()
