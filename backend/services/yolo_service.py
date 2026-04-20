"""
backend/services/yolo_service.py
YOLOv8 inference service for license plate detection.

Singleton pattern: one instance created at app startup in main.py.
"""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class YOLOService:
    """
    Wraps Ultralytics YOLOv8 for license plate detection.

    Usage:
        service = YOLOService(model_path="ml_models/yolov8n_plate.pt")
        detections = service.detect(frame_bgr)
        annotated  = service.annotate(frame_bgr, detections)
    """

    def __init__(self, model_path: str | Path, conf_threshold: float = 0.45):
        self.conf_threshold = conf_threshold
        self._model = None
        self._load_model(Path(model_path))

    def _load_model(self, model_path: Path) -> None:
        """Load YOLO model. Falls back to yolov8n.pt if custom model not found."""
        from ultralytics import YOLO  # deferred import — heavy library

        if model_path.exists():
            logger.info(f"Loading YOLO model: {model_path}")
            self._model = YOLO(str(model_path))
        else:
            # Fallback: use default nano model (downloads automatically)
            logger.warning(
                f"Custom model not found at {model_path}, "
                "falling back to yolov8n.pt (COCO pretrained)"
            )
            self._model = YOLO("yolov8n.pt")

        logger.info("YOLO model loaded successfully")

    # ─── Core inference ──────────────────────────────────────────────────────

    def detect(self, image: np.ndarray) -> list[dict]:
        """
        Run detection on a BGR numpy image.

        Returns:
            List of dicts:
            {
                "bbox":        [x1, y1, x2, y2],
                "confidence":  float,
                "crop":        np.ndarray (BGR),
                "class_id":    int,
                "class_name":  str,
            }
        """
        results = self._model(image, conf=self.conf_threshold, verbose=False)
        detections: list[dict] = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf     = float(box.conf[0])
                cls_id   = int(box.cls[0])
                cls_name = self._model.names.get(cls_id, "unknown")

                # Clamp to image boundaries
                h, w = image.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                crop = image[y1:y2, x1:x2]

                detections.append({
                    "bbox":       [x1, y1, x2, y2],
                    "confidence": conf,
                    "crop":       crop,
                    "class_id":   cls_id,
                    "class_name": cls_name,
                })

        logger.debug(f"YOLO detected {len(detections)} plate(s)")
        return detections

    def detect_from_path(self, image_path: str | Path) -> list[dict]:
        """Load an image from disk and run detect()."""
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        return self.detect(img)

    def detect_from_frame(self, frame: np.ndarray) -> list[dict]:
        """Alias for detect() — for stream compatibility."""
        return self.detect(frame)

    # ─── Annotation ──────────────────────────────────────────────────────────

    def annotate(
        self,
        image: np.ndarray,
        detections: list[dict],
        color: tuple = (0, 200, 100),
        thickness: int = 2,
    ) -> np.ndarray:
        """
        Draw bounding boxes and plate labels on *image*.

        Args:
            image:      Original BGR image (not mutated — copy is made).
            detections: List of detection dicts (from detect()).
            color:      BGR color for bounding boxes.
            thickness:  Line thickness.

        Returns:
            Annotated BGR image.
        """
        annotated = image.copy()

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            plate_text = det.get("plate_text", "")
            conf       = det.get("confidence", 0)

            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            # Build label
            label = f"{plate_text} {conf:.0%}" if plate_text else f"{conf:.0%}"
            label_size, baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
            )
            lw, lh = label_size

            # Background rectangle for label
            cv2.rectangle(
                annotated,
                (x1, y1 - lh - baseline - 4),
                (x1 + lw + 4, y1),
                color,
                cv2.FILLED,
            )

            # Label text
            cv2.putText(
                annotated,
                label,
                (x1 + 2, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        return annotated
