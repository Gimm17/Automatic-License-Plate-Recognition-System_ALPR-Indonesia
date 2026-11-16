"""
Download and test license plate detection models.
Tests on real Kemenhub HLS frame and picks the best one.
"""
import sys, os, shutil, time
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from huggingface_hub import hf_hub_download
from ultralytics import YOLO
import cv2, numpy as np

dest_dir = Path("ml_models")
dest_dir.mkdir(exist_ok=True)

MODELS = [
    ("Koushim/yolov8-license-plate-detection", "best.pt", "koushim_plate.pt"),
    ("nguyenluat/yolov8n-license-plate-vn",    "best.pt", "nguyen_plate_vn.pt"),
]

print("=" * 60)
print("Downloading License Plate Detection Models")
print("=" * 60)

# ── Download all models ────────────────────────────────────────────────────────
downloaded = []
for repo_id, filename, local_name in MODELS:
    dest = dest_dir / local_name
    if dest.exists():
        print(f"\n✓ Already exists: {local_name}")
        downloaded.append((local_name, dest))
        continue
    try:
        print(f"\nDownloading: {repo_id}...")
        local = hf_hub_download(repo_id=repo_id, filename=filename)
        shutil.copy(local, dest)
        size_mb = dest.stat().st_size / 1e6
        print(f"  ✓ Saved: {local_name} ({size_mb:.1f} MB)")
        downloaded.append((local_name, dest))
    except Exception as e:
        print(f"  ✗ Failed: {e}")

# ── Grab a real frame from Kemenhub stream ─────────────────────────────────────
print("\nGrabbing test frame from Kemenhub HLS stream...")
url = "https://mitradarat-vidstream.dephub.go.id/stream/RNCKCCTVRANCAEKEKB/index.m3u8"
frame = None
cap = cv2.VideoCapture(url)
for _ in range(5):
    cap.grab()
ret, frame = cap.read()
cap.release()

if frame is None:
    print("  ✗ Could not grab frame, using blank test image")
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Draw fake plate region for testing
    cv2.rectangle(frame, (300, 400), (600, 480), (200, 200, 200), -1)
    cv2.putText(frame, "B 1234 XYZ", (310, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
else:
    print(f"  ✓ Frame: {frame.shape}")
    cv2.imwrite("ml_models/test_frame.jpg", frame)

# ── Test each model ───────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Testing models on frame")
print("=" * 60)

best_model = None
best_count = -1

for local_name, path in downloaded:
    try:
        print(f"\nModel: {local_name}")
        model = YOLO(str(path))

        # Try different confidence thresholds
        for conf in [0.1, 0.25, 0.5]:
            results = model(frame, conf=conf, verbose=False)
            count = sum(len(r.boxes) for r in results)
            if count > 0:
                print(f"  conf={conf}: {count} detection(s)")
                # Save annotated frame
                for r in results:
                    ann = r.plot()
                    cv2.imwrite(f"ml_models/test_{local_name}_conf{int(conf*100)}.jpg", ann)
                    if best_count < count:
                        best_count = count
                        best_model = path
                break
        else:
            print(f"  No plates detected at any confidence")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
if best_model:
    final = dest_dir / "yolov8n_plate.pt"
    shutil.copy(best_model, final)
    print(f"✅ Best model: {best_model.name} ({best_count} detections)")
    print(f"   Saved as: {final}")
else:
    # Default to first downloaded
    if downloaded:
        final = dest_dir / "yolov8n_plate.pt"
        shutil.copy(downloaded[0][1], final)
        print(f"⚠️  No plates detected in test frame (may be no plates visible now)")
        print(f"   Using: {downloaded[0][0]} as default")
        print(f"   Saved as: {final}")
    else:
        print("✗ No models downloaded!")

print()
print("→ Restart uvicorn to use the new model")
