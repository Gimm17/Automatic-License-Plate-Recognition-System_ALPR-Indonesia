"""
Test license plate detection on Kemenhub stream with various settings.
Saves annotated frames so you can visually check what YOLO sees.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import cv2, numpy as np
from pathlib import Path
from ultralytics import YOLO
from config import settings

print("=== Plate Detection Visual Test ===\n")

# Load model
print("Loading model:", settings.yolo_model_full_path)
model = YOLO(str(settings.yolo_model_full_path))
print("Model classes:", model.names)

# Grab multiple frames
url = "https://mitradarat-vidstream.dephub.go.id/stream/RNCKCCTVRANCAEKEKB/index.m3u8"
print(f"\nGrabbing frames from stream...")

out_dir = Path("ml_models/test_results")
out_dir.mkdir(exist_ok=True)

for attempt in range(3):
    cap = cv2.VideoCapture(url)
    # Skip ahead to get different timestamps
    for _ in range(attempt * 10 + 3):
        cap.grab()
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print(f"  Frame {attempt+1}: FAILED")
        continue

    print(f"\nFrame {attempt+1}: {frame.shape}")

    # Test at very low confidence
    for conf in [0.01, 0.05, 0.1, 0.25]:
        results = model(frame, conf=conf, verbose=False)
        dets = results[0].boxes
        count = len(dets)
        if count > 0:
            print(f"  conf={conf:.2f}: {count} detection(s)!")
            for box in dets:
                print(f"    bbox={[int(v) for v in box.xyxy[0].tolist()]} conf={float(box.conf[0]):.3f}")

            # Save annotated
            ann = results[0].plot()
            out = out_dir / f"frame{attempt+1}_conf{int(conf*100)}.jpg"
            cv2.imwrite(str(out), ann)
            print(f"  Saved: {out}")
            break
    else:
        # No detections at any confidence — save raw frame anyway
        out = out_dir / f"frame{attempt+1}_raw.jpg"
        cv2.imwrite(str(out), frame)
        print(f"  No plates detected. Raw frame saved: {out}")
        # Also save a zoomed-in region (bottom half where road is)
        h, w = frame.shape[:2]
        lower = frame[h//2:, :]
        out2 = out_dir / f"frame{attempt+1}_lower.jpg"
        cv2.imwrite(str(out2), lower)

print(f"\nAll test images saved to: {out_dir.resolve()}")
print("Open them to see what the camera captures!")
