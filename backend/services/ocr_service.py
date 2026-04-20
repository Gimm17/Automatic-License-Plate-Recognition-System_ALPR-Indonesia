"""
backend/services/ocr_service.py
PaddleOCR wrapper for reading license plate text from cropped images.

Singleton pattern: initialized ONCE at startup to avoid per-request overhead.
"""

import logging
from typing import Optional

import numpy as np
from services.preprocessor import enhance_for_ocr

logger = logging.getLogger(__name__)


class OCRService:
    """
    Wraps PaddleOCR for reading text from license plate crops.

    Design:
    - Initialized once at startup (slow init ≈ 3-5s).
    - read_plate() is fast per-call after warm-up.
    - Falls back gracefully if PaddleOCR is unavailable.
    """

    _instance: Optional["OCRService"] = None

    def __init__(self, language: str = "en"):
        self._ocr = None
        self._language = language
        self._available = False
        self._initialize()

    def _initialize(self) -> None:
        """Initialize PaddleOCR. Logs error but does not crash if unavailable."""
        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self._language,
                show_log=False,
                use_gpu=False,         # Change to True if GPU available
                enable_mkldnn=False,   # Disable MKL-DNN for compatibility
            )
            self._available = True
            logger.info("PaddleOCR initialized successfully")
        except ImportError:
            logger.warning(
                "PaddleOCR not installed. OCR will return empty results. "
                "Install with: pip install paddlepaddle paddleocr"
            )
        except Exception as e:
            logger.error(f"PaddleOCR initialization failed: {e}")

    # ─── Public API ───────────────────────────────────────────────────────────

    def read_plate(self, crop: np.ndarray) -> dict:
        """
        Read license plate text from a crop image.

        Args:
            crop: BGR numpy array of the license plate region.

        Returns:
            {
                "text":       str,   # cleaned uppercase plate text
                "confidence": float, # 0.0 – 1.0
            }
        """
        if not self._available or self._ocr is None:
            return {"text": "", "confidence": 0.0}

        if crop is None or crop.size == 0:
            return {"text": "", "confidence": 0.0}

        try:
            enhanced = self._enhance(crop)
            result   = self._ocr.ocr(enhanced, cls=True)

            if not result or result[0] is None:
                return {"text": "", "confidence": 0.0}

            texts: list[tuple[str, float]] = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text, conf = line[1]
                    texts.append((str(text), float(conf)))

            if not texts:
                return {"text": "", "confidence": 0.0}

            # Prefer highest confidence
            best_text, best_conf = max(texts, key=lambda x: x[1])

            # Clean: uppercase, strip dots and extra spaces
            cleaned = best_text.upper().replace(".", "").strip()
            # Remove isolated non-alphanumeric chars
            import re
            cleaned = re.sub(r"[^A-Z0-9\s]", "", cleaned).strip()

            return {"text": cleaned, "confidence": best_conf}

        except Exception as e:
            logger.error(f"OCR error: {e}")
            return {"text": "", "confidence": 0.0}

    def is_available(self) -> bool:
        return self._available

    # ─── Private ──────────────────────────────────────────────────────────────

    def _enhance(self, img: np.ndarray) -> np.ndarray:
        """Run preprocessor before OCR."""
        try:
            return enhance_for_ocr(img)
        except Exception as e:
            logger.warning(f"Preprocessing failed, using raw crop: {e}")
            return img
