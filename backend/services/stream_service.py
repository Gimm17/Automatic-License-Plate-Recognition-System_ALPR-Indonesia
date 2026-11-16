"""
backend/services/stream_service.py
RTSP/webcam capture and real-time ALPR WebSocket streaming.
"""

import asyncio
import base64
import logging
import time

import cv2
import numpy as np
from fastapi import WebSocket

from config import settings
from database import SessionLocal
from services.alpr_pipeline import process_frame

logger = logging.getLogger(__name__)


class StreamService:
    """Handles live video streaming and periodic ALPR inference."""

    def __init__(self, yolo_service, ocr_service):
        self.yolo = yolo_service
        self.ocr = ocr_service
        self._active_streams: dict[int, int] = {}

    async def start_stream(
        self,
        websocket: WebSocket,
        camera_id: int,
        source: str,
        process_every: int = settings.PROCESS_EVERY_N_FRAMES,
        jpeg_quality: int = settings.STREAM_JPEG_QUALITY,
        db=None,
    ) -> None:
        """Read frames, send JPEG frames, and attach detection metadata."""
        await websocket.accept()

        cap_source = int(source) if source.isdigit() else source
        cap = cv2.VideoCapture(cap_source)
        if not cap.isOpened():
            await websocket.send_json({"type": "error", "message": f"Cannot open stream source: {source}"})
            await websocket.close()
            return

        self._mark_stream_started(camera_id)
        logger.info("Stream started: camera_id=%s source=%s", camera_id, source)
        await websocket.send_json({"type": "connected", "camera_id": camera_id})

        frame_count = 0
        last_detection: list[dict] = []
        t_start = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Stream ended or frame read failed: camera_id=%s", camera_id)
                    break

                frame_count += 1
                current_detections = last_detection
                image_height, image_width = frame.shape[:2]

                if frame_count % process_every == 0:
                    processed = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self._process_frame,
                        frame.copy(),
                        camera_id,
                    )
                    current_detections = processed["detections"]
                    last_detection = current_detections
                    if current_detections:
                        frame = self.yolo.annotate(frame, processed["raw_detections"])

                elapsed = time.time() - t_start
                fps = round(frame_count / elapsed, 1) if elapsed > 0 else 0
                await websocket.send_json(
                    {
                        "type": "frame",
                        "frame": _encode_frame(frame, jpeg_quality),
                        "detections": current_detections,
                        "frame_count": frame_count,
                        "fps_display": fps,
                        "camera_id": camera_id,
                        "image_width": image_width,
                        "image_height": image_height,
                    }
                )
                await asyncio.sleep(0.033)
        except Exception as exc:
            logger.error("Stream error camera_id=%s: %s", camera_id, exc)
            try:
                await websocket.send_json({"type": "error", "message": str(exc)})
            except Exception:
                pass
        finally:
            self._mark_stream_stopped(camera_id)
            cap.release()
            logger.info("Stream stopped: camera_id=%s total_frames=%s", camera_id, frame_count)
            try:
                await websocket.close()
            except Exception:
                pass

    def is_streaming(self, camera_id: int) -> bool:
        return self._active_streams.get(camera_id, 0) > 0

    def _mark_stream_started(self, camera_id: int) -> None:
        self._active_streams[camera_id] = self._active_streams.get(camera_id, 0) + 1

    def _mark_stream_stopped(self, camera_id: int) -> None:
        count = self._active_streams.get(camera_id, 0) - 1
        if count > 0:
            self._active_streams[camera_id] = count
        else:
            self._active_streams.pop(camera_id, None)

    def _process_frame(self, frame: np.ndarray, camera_id: int) -> dict:
        """Run the shared ALPR pipeline in a worker thread."""
        db = SessionLocal()
        try:
            result = process_frame(
                frame,
                yolo=self.yolo,
                ocr=self.ocr,
                db=db,
                camera_id=camera_id,
                source_type="stream",
                save_crops=False,
                persist=True,
            )
            db.commit()
            return result
        except Exception as exc:
            logger.warning("Stream frame processing failed: %s", exc)
            db.rollback()
            return {"detections": [], "raw_detections": [], "image_width": 0, "image_height": 0}
        finally:
            db.close()


def _encode_frame(frame: np.ndarray, quality: int = 60) -> str:
    """Encode a BGR frame to base64 JPEG string."""
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode(".jpg", frame, encode_params)
    return base64.b64encode(buffer).decode("utf-8")
