"""
backend/utils/image_utils.py
Image helper functions: base64 encoding, saving, resizing.
"""

import base64
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def image_to_base64(img: np.ndarray, quality: int = 85) -> str:
    """
    Encode a numpy BGR image to a base64 JPEG string.
    Returns a data-URI safe string (without the data:image/jpeg;base64, prefix).
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success, buffer = cv2.imencode(".jpg", img, encode_params)
    if not success:
        raise ValueError("Failed to encode image to JPEG")
    return base64.b64encode(buffer).decode("utf-8")


def base64_to_image(b64_str: str) -> np.ndarray:
    """
    Decode a base64 string (with or without data-URI prefix) to numpy BGR image.
    """
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    raw = base64.b64decode(b64_str)
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode base64 string to image")
    return img


def save_image(img: np.ndarray, directory: Path, filename: Optional[str] = None) -> Path:
    """
    Save a numpy image to *directory* with the given *filename*.
    If *filename* is None, a UUID-based name is generated.
    Returns the full Path of the saved file.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"{uuid.uuid4().hex}.jpg"

    dest = directory / filename
    cv2.imwrite(str(dest), img)
    return dest


def resize_for_display(img: np.ndarray, max_width: int = 800) -> np.ndarray:
    """
    Proportionally resize *img* so its width does not exceed *max_width*.
    If the image is already smaller, returns it unchanged.
    """
    h, w = img.shape[:2]
    if w <= max_width:
        return img
    scale = max_width / w
    new_w = max_width
    new_h = int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def crop_region(img: np.ndarray, bbox: list[int]) -> np.ndarray:
    """
    Crop *img* using a [x1, y1, x2, y2] bounding box.
    Clamps coordinates to image boundaries.
    """
    h, w = img.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return img[y1:y2, x1:x2]
