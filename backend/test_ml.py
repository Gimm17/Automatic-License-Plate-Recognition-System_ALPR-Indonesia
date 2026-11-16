"""Quick end-to-end test of ML stack."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("=== Quick ML Stack Test ===")

from services.yolo_service import YOLOService
from services.ocr_service import OCRService
from config import settings
import cv2

print("1. Loading YOLO...")
yolo = YOLOService(model_path=settings.yolo_model_full_path, conf_threshold=0.25)
print("   YOLO loaded OK")

print("2. Test frame grab from HLS...")
url = "https://mitradarat-vidstream.dephub.go.id/stream/RNCKCCTVRANCAEKEKB/index.m3u8"
cap = cv2.VideoCapture(url)
cap.grab(); cap.grab(); cap.grab()
ret, frame = cap.read()
cap.release()
print(f"   Frame: {frame.shape if ret else 'FAILED'}")

if ret and frame is not None:
    print("3. Running YOLO on frame...")
    dets = yolo.detect(frame)
    print(f"   YOLO raw detections: {len(dets)} objects")
    for d in dets[:5]:
        print(f"     class={d['class_name']} conf={d['confidence']:.2f} bbox={d['bbox']}")

print()
print("4. Testing PaddleOCR init (downloads models first time - wait ~1 min)...")
try:
    ocr = OCRService(language="en")
    print(f"   OCR available: {ocr.is_available()}")
    if ret and frame is not None and dets:
        x1,y1,x2,y2 = dets[0]["bbox"]
        crop = frame[y1:y2, x1:x2]
        if crop.size > 0:
            result = ocr.read_plate(crop)
            print(f"   OCR result: {result}")
except Exception as e:
    print(f"   OCR error: {type(e).__name__}: {str(e)[:200]}")

print()
print("=== Test complete ===")
