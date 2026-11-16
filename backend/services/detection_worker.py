"""
backend/services/detection_worker.py
Optional background detection worker for active camera streams.
"""

import asyncio
import logging
from typing import Optional

import cv2
import numpy as np

from database import SessionLocal
from services.alpr_pipeline import process_frame

logger = logging.getLogger(__name__)

SAMPLE_INTERVAL_S = 5
GRAB_SKIP = 3


class DetectionWorker:
    """Background task manager; disabled unless ENABLE_DETECTION_WORKER=true."""

    def __init__(self, yolo_service, ocr_service):
        self.yolo = yolo_service
        self.ocr = ocr_service
        self._tasks: dict[int, asyncio.Task] = {}
        self._sources: dict[int, str] = {}
        self._running = False

    def start_all(self, cameras: list) -> None:
        self._running = True
        for cam in cameras:
            self.sync_camera(cam)

    def start_camera(self, camera_id: int, stream_url: str) -> None:
        self._running = True
        existing = self._tasks.get(camera_id)
        if existing and not existing.done() and self._sources.get(camera_id) == stream_url:
            return
        self.stop_camera(camera_id)
        task = asyncio.create_task(self._camera_loop(camera_id, stream_url), name=f"detect_cam_{camera_id}")
        self._tasks[camera_id] = task
        self._sources[camera_id] = stream_url
        logger.info("[DetectionWorker] Started task for camera_id=%s", camera_id)

    def sync_camera(self, camera) -> None:
        if getattr(camera, "is_active", False) and getattr(camera, "rtsp_url", None):
            self.start_camera(camera.id, camera.rtsp_url)
        else:
            self.stop_camera(camera.id)

    def stop_camera(self, camera_id: int) -> None:
        task = self._tasks.pop(camera_id, None)
        self._sources.pop(camera_id, None)
        if task and not task.done():
            task.cancel()
            logger.info("[DetectionWorker] Stopped task for camera_id=%s", camera_id)

    def stop_all(self) -> None:
        self._running = False
        for camera_id, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
        self._tasks.clear()
        self._sources.clear()
        logger.info("[DetectionWorker] All tasks stopped")

    async def _camera_loop(self, camera_id: int, stream_url: str) -> None:
        consecutive_errors = 0
        max_errors = 10
        logger.info("[Cam %s] Detection loop started: %s", camera_id, stream_url[:80])

        while self._running:
            try:
                frame = await asyncio.get_event_loop().run_in_executor(None, self._grab_frame, stream_url)
                if frame is None:
                    consecutive_errors += 1
                    logger.warning("[Cam %s] Frame grab failed (%s/%s)", camera_id, consecutive_errors, max_errors)
                    await asyncio.sleep(60 if consecutive_errors >= max_errors else SAMPLE_INTERVAL_S)
                    if consecutive_errors >= max_errors:
                        consecutive_errors = 0
                    continue

                consecutive_errors = 0
                detections = await asyncio.get_event_loop().run_in_executor(None, self._detect, camera_id, frame)
                if detections:
                    logger.info(
                        "[Cam %s] Detected %s plate(s): %s",
                        camera_id,
                        len(detections),
                        [d["plate_text"] for d in detections],
                    )
            except asyncio.CancelledError:
                logger.info("[Cam %s] Detection task cancelled", camera_id)
                break
            except Exception as exc:
                logger.exception("[Cam %s] Unexpected error: %s", camera_id, exc)
                consecutive_errors += 1

            await asyncio.sleep(SAMPLE_INTERVAL_S)

    def _grab_frame(self, stream_url: str) -> Optional[np.ndarray]:
        try:
            source = int(stream_url) if str(stream_url).isdigit() else stream_url
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                return None
            for _ in range(GRAB_SKIP):
                cap.grab()
            ret, frame = cap.read()
            cap.release()
            return frame if ret and frame is not None else None
        except Exception as exc:
            logger.debug("[grab_frame] Error: %s", exc)
            return None

    def _detect(self, camera_id: int, frame: np.ndarray) -> list[dict]:
        if self.yolo is None or self.ocr is None:
            return []

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
            return result["detections"]
        except Exception as exc:
            logger.exception("[detect] camera_id=%s error: %s", camera_id, exc)
            db.rollback()
            return []
        finally:
            db.close()
