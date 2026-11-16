"""
backend/services/ocr_service.py
OCR wrapper for reading license plate text.

PaddleOCR is the default engine because it is included in requirements.txt.
EasyOCR remains an optional fallback.
"""

import logging
import re

import numpy as np
from services.preprocessor import enhance_for_ocr

logger = logging.getLogger(__name__)


class OCRService:
    """Initialized once at startup; read_plate() returns text/confidence."""

    def __init__(self, language: str = "en"):
        self._reader = None
        self._engine = None
        self._available = False
        self._language = language
        self._initialize()

    def _initialize(self) -> None:
        """Try PaddleOCR first, then optional EasyOCR."""
        try:
            from paddleocr import PaddleOCR
            import paddleocr as _poc

            ver_str = getattr(_poc, "__version__", "2.0")
            major = int(ver_str.split(".")[0])
            if major >= 3:
                logger.warning("PaddleOCR v3 detected; trying EasyOCR fallback.")
            else:
                self._reader = PaddleOCR(
                    use_angle_cls=True,
                    lang=self._language,
                    show_log=False,
                    use_gpu=False,
                    enable_mkldnn=False,
                )
                self._engine = "paddleocr"
                self._available = True
                logger.info("OCRService initialized with PaddleOCR")
                return
        except ImportError:
            logger.debug("PaddleOCR not installed, trying EasyOCR...")
        except Exception as exc:
            logger.warning("PaddleOCR initialization failed: %s; trying EasyOCR...", exc)

        try:
            import easyocr

            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            self._engine = "easyocr"
            self._available = True
            logger.info("OCRService initialized with EasyOCR")
        except ImportError:
            logger.warning("No OCR engine available. Install paddleocr or optional easyocr.")
        except Exception as exc:
            logger.error("EasyOCR initialization failed: %s", exc)

    def read_plate(self, crop: np.ndarray) -> dict:
        """Read license plate text from a crop image."""
        if not self._available or self._reader is None:
            return {"text": "", "confidence": 0.0}
        if crop is None or crop.size == 0:
            return {"text": "", "confidence": 0.0}

        try:
            enhanced = self._enhance(crop)
            if self._engine == "easyocr":
                return self._read_easyocr(enhanced)
            return self._read_paddleocr(enhanced)
        except Exception as exc:
            logger.error("OCR error: %s", exc)
            return {"text": "", "confidence": 0.0}

    def is_available(self) -> bool:
        return self._available

    def engine_name(self) -> str:
        return self._engine or "none"

    def _read_easyocr(self, img: np.ndarray) -> dict:
        results = self._reader.readtext(img)
        if not results:
            return {"text": "", "confidence": 0.0}

        texts = [(str(r[1]), float(r[2])) for r in results if r[1]]
        if not texts:
            return {"text": "", "confidence": 0.0}

        best_text, best_conf = max(texts, key=lambda x: x[1])
        return {"text": self._clean_plate(best_text), "confidence": best_conf}

    def _read_paddleocr(self, img: np.ndarray) -> dict:
        result = self._reader.ocr(img, cls=True)
        texts: list[tuple[str, float]] = []

        try:
            if result and result[0] is not None:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text_info = line[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) == 2:
                            text, conf = text_info
                            texts.append((str(text), float(conf)))
        except Exception as exc:
            logger.debug("PaddleOCR parse error: %s", exc)

        if not texts:
            return {"text": "", "confidence": 0.0}

        best_text, best_conf = max(texts, key=lambda x: x[1])
        return {"text": self._clean_plate(best_text), "confidence": best_conf}

    def _clean_plate(self, text: str) -> str:
        cleaned = text.upper().replace(".", "").replace("-", "").strip()
        return re.sub(r"[^A-Z0-9\s]", "", cleaned).strip()

    def _enhance(self, img: np.ndarray) -> np.ndarray:
        try:
            return enhance_for_ocr(img)
        except Exception as exc:
            logger.warning("Preprocessing failed, using raw crop: %s", exc)
            return img
