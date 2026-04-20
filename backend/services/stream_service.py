"""
backend/services/stream_service.py
Fase 2 — RTSP stream capture and real-time ALPR frame processing.

Manages multiple concurrent camera streams and sends results over WebSocket.
"""

import asyncio
import base64
import logging
import time
from typing import Optional

import cv2
import numpy as np
from fastapi import WebSocket

from config import settings
from services.plate_validator import validate_plate

logger = logging.getLogger(__name__)


class StreamService:
    """
    Handles live RTSP/webcam streaming with per-frame ALPR detection.

    Design:
    - start_stream() runs an async loop, reading frames from OpenCV.
    - Sends raw frame as base64 JPEG every iteration (~30fps display).
    - Runs YOLO+OCR only every PROCESS_EVERY_N_FRAMES frames to conserve CPU.
    - Sends detection data back over WebSocket as JSON.

    WebSocket message format:
        {
            "type":       "frame",
            "frame":      "<base64 JPEG>",
            "detections": [
                {
                    "plate_text":    str,
                    "confidence":    float,
                    "ocr_confidence": float,
                    "bbox":          [x1,y1,x2,y2],
                    "region":        str,
                    "status":        str,
                }
            ],
            "frame_count": int,
            "fps_display": float,
        }
    """

    def __init__(self, yolo_service, ocr_service):
        self.yolo = yolo_service
        self.ocr  = ocr_service
        # Track active streams: camera_id → asyncio.Task
        self._active_streams: dict[int, asyncio.Task] = {}

    # ─── Public API ──────────────────────────────────────────────────────────

    async def start_stream(
        self,
        websocket: WebSocket,
        camera_id: int,
        source: str,                    # RTSP URL or "0" for webcam
        process_every: int = settings.PROCESS_EVERY_N_FRAMES,
        jpeg_quality: int  = settings.STREAM_JPEG_QUALITY,
        db=None,                        # Optional DB session for saving detections
    ) -> None:
        """
        Main stream loop: read frames → encode → send over WebSocket.

        Args:
            websocket:     Open FastAPI WebSocket connection.
            camera_id:     ID of the camera record.
            source:        RTSP URL string or device index as string ("0").
            process_every: Run ALPR every N frames.
            jpeg_quality:  JPEG encoding quality (1-100).
            db:            Optional SQLAlchemy session for persisting detections.
        """
        await websocket.accept()

        # Allow device index (webcam)
        cap_source = int(source) if source.isdigit() else source
        cap = cv2.VideoCapture(cap_source)

        if not cap.isOpened():
            await websocket.send_json({
                "type":    "error",
                "message": f"Cannot open stream source: {source}",
            })
            await websocket.close()
            return

        logger.info(f"Stream started: camera_id={camera_id} source={source}")
        await websocket.send_json({"type": "connected", "camera_id": camera_id})

        frame_count    = 0
        last_detection: list[dict] = []
        t_start        = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Stream ended or frame read failed: camera_id={camera_id}")
                    break

                frame_count += 1
                current_detections = last_detection  # use previous detections between processing frames

                # ── Run ALPR every N frames ──────────────────────────────
                if frame_count % process_every == 0:
                    current_detections = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self._process_frame,
                        frame,
                        camera_id,
                        db,
                    )
                    last_detection = current_detections

                    # Annotate frame with boxes
                    if current_detections:
                        frame = self.yolo.annotate(frame, [
                            {**d, "confidence": d.get("confidence", 0)}
                            for d in current_detections
                        ])

                # ── Encode frame as base64 JPEG ───────────────────────────
                frame_b64 = _encode_frame(frame, jpeg_quality)

                # ── Calculate display FPS ─────────────────────────────────
                elapsed = time.time() - t_start
                fps     = round(frame_count / elapsed, 1) if elapsed > 0 else 0

                # ── Send over WebSocket ───────────────────────────────────
                await websocket.send_json({
                    "type":        "frame",
                    "frame":       frame_b64,
                    "detections":  current_detections,
                    "frame_count": frame_count,
                    "fps_display": fps,
                    "camera_id":   camera_id,
                })

                # Throttle to ~30fps display rate
                await asyncio.sleep(0.033)

        except Exception as e:
            logger.error(f"Stream error camera_id={camera_id}: {e}")
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass
        finally:
            cap.release()
            logger.info(f"Stream stopped: camera_id={camera_id} total_frames={frame_count}")
            try:
                await websocket.close()
            except Exception:
                pass

    def is_streaming(self, camera_id: int) -> bool:
        return camera_id in self._active_streams

    # ─── Private ─────────────────────────────────────────────────────────────

    def _process_frame(self, frame: np.ndarray, camera_id: int, db) -> list[dict]:
        """
        Run YOLO + OCR + validation on a single frame.
        This is run in a thread executor to avoid blocking the event loop.
        """
        detections: list[dict] = []

        try:
            raw = self.yolo.detect(frame)
        except Exception as e:
            logger.error(f"YOLO detect error: {e}")
            return []

        for det in raw:
            crop = det.get("crop")
            bbox = det.get("bbox", [0, 0, 0, 0])
            conf = det.get("confidence", 0)

            if crop is None or crop.size == 0:
                continue

            try:
                ocr_result = self.ocr.read_plate(crop)
            except Exception:
                ocr_result = {"text": "", "confidence": 0.0}

            plate_text = ocr_result.get("text", "")
            ocr_conf   = ocr_result.get("confidence", 0.0)

            validation = validate_plate(plate_text) if plate_text else {
                "plate": "", "valid": False,
                "status": "ocr_failed", "region": "", "region_code": "",
            }
            status = validation["status"] if plate_text else "ocr_failed"

            detections.append({
                "plate_text":    validation.get("plate", plate_text),
                "plate_raw":     plate_text,
                "confidence":    round(conf, 3),
                "ocr_confidence": round(ocr_conf, 3),
                "bbox":          bbox,
                "region":        validation.get("region", ""),
                "region_code":   validation.get("region_code", ""),
                "status":        status,
                "valid":         validation.get("valid", False),
                "camera_id":     camera_id,
            })

            # Persist to DB in background (best-effort)
            if db and plate_text:
                try:
                    from models.detection import Detection
                    record = Detection(
                        camera_id      = camera_id,
                        plate_text     = validation.get("plate") or plate_text,
                        plate_raw      = plate_text,
                        confidence     = conf,
                        ocr_confidence = ocr_conf,
                        region         = validation.get("region", ""),
                        region_code    = validation.get("region_code", ""),
                        source_type    = "stream",
                        status         = status,
                    )
                    db.add(record)
                    db.commit()
                except Exception as db_err:
                    logger.warning(f"DB persist error (stream): {db_err}")
                    db.rollback()

        return detections


def _encode_frame(frame: np.ndarray, quality: int = 60) -> str:
    """Encode a BGR frame to base64 JPEG string."""
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode(".jpg", frame, encode_params)
    return base64.b64encode(buffer).decode("utf-8")
