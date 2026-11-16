"""
Update camera RTSP/stream URL for Kemenhub camera.

The API endpoint https://hubnet.kemenhub.go.id/backend/api/show-cctv?...
returns an HTML page with an iframe pointing to the REAL stream URL.

Real HLS URL: https://mitradarat-vidstream.dephub.go.id/stream/RNCKCCTVRANCAEKEKB/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_db, engine
from models.camera import Camera
from sqlalchemy.orm import Session

def update_camera_urls():
    db: Session = next(get_db())
    
    cameras = db.query(Camera).all()
    print(f"\n[DB] Kamera dalam database ({len(cameras)} total):\n")
    for cam in cameras:
        print(f"  ID={cam.id} | name='{cam.name}' | is_active={cam.is_active}")
        print(f"    URL: {cam.rtsp_url[:80] if cam.rtsp_url else '(kosong)'}...")
        print()
    
    # Fix: kamera yang pakai URL API Kemenhub (HTML page), ganti ke HLS langsung
    WRONG_PREFIX  = "https://hubnet.kemenhub.go.id/backend/api/show-cctv"
    CORRECT_URL   = "https://mitradarat-vidstream.dephub.go.id/stream/RNCKCCTVRANCAEKEKB/"
    
    updated = 0
    for cam in cameras:
        if cam.rtsp_url and cam.rtsp_url.startswith(WRONG_PREFIX):
            print(f"[UPDATE] Updating '{cam.name}' (ID={cam.id}):")
            print(f"   FROM: {cam.rtsp_url[:80]}...")
            print(f"   TO:   {CORRECT_URL}")
            cam.rtsp_url  = CORRECT_URL
            cam.is_active = True   # ensure it's active
            updated += 1
    
    if updated:
        db.commit()
        print(f"\n[OK] {updated} kamera berhasil diupdate!")
    else:
        print("[INFO] Tidak ada URL yang perlu diupdate (sudah benar atau tidak ditemukan)")
    
    db.close()

if __name__ == "__main__":
    update_camera_urls()
