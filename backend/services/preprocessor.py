"""
backend/services/preprocessor.py
OpenCV image preprocessing for optimal OCR performance.
"""

import cv2
import numpy as np


def enhance_for_ocr(img: np.ndarray) -> np.ndarray:
    """
    Full preprocessing pipeline for license plate crops before OCR.

    Pipeline:
        1. Upscale if width < 200px (bilinear interpolation)
        2. Convert to grayscale
        3. Apply fastNlMeansDenoising (non-local means)
        4. Sharpen with a 3x3 kernel
        5. Convert back to BGR (PaddleOCR expects 3-channel)

    Args:
        img: BGR numpy array from OpenCV.

    Returns:
        Preprocessed BGR numpy array.
    """
    if img is None or img.size == 0:
        raise ValueError("Input image is empty or None")

    # ── 1. Upscale if too small ───────────────────────────────────────────
    h, w = img.shape[:2]
    if w < 200:
        scale = 200 / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # ── 2. Grayscale ─────────────────────────────────────────────────────
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # ── 3. Denoise ───────────────────────────────────────────────────────
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # ── 4. Sharpen ───────────────────────────────────────────────────────
    sharpen_kernel = np.array([[0, -1, 0],
                                [-1, 5, -1],
                                [0, -1, 0]], dtype=np.float32)
    sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)

    # ── 5. Convert back to BGR ────────────────────────────────────────────
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)


def deskew(img: np.ndarray) -> np.ndarray:
    """
    Attempt to deskew (straighten) a plate crop using Hough transform.
    Falls back to original image if angle detection fails.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 80)

    if lines is None:
        return img

    angles = []
    for line in lines[:10]:
        rho, theta = line[0]
        angle = (theta - np.pi / 2) * (180 / np.pi)
        if abs(angle) < 30:
            angles.append(angle)

    if not angles:
        return img

    median_angle = float(np.median(angles))
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), median_angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
