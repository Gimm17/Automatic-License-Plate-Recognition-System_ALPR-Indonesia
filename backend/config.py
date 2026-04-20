"""
backend/config.py
Application configuration loaded from environment variables (.env).
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # ─── App ────────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_SECRET_KEY: str = "change-me-in-production"

    # ─── Database ───────────────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "alpr_db"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    # ─── CORS ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ─── ML Models ──────────────────────────────────────────────────────────────
    YOLO_MODEL_PATH: str = "ml_models/yolov8n_plate.pt"
    YOLO_CONFIDENCE: float = 0.45
    OCR_LANGUAGE: str = "en"

    @property
    def yolo_model_full_path(self) -> Path:
        """Resolve YOLO model path relative to backend directory."""
        p = Path(self.YOLO_MODEL_PATH)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p

    # ─── Storage ────────────────────────────────────────────────────────────────
    STORAGE_PATH: str = "storage"
    MAX_UPLOAD_SIZE_MB: int = 50

    @property
    def storage_dir(self) -> Path:
        return BASE_DIR / self.STORAGE_PATH

    @property
    def temp_dir(self) -> Path:
        return self.storage_dir / "temp"

    @property
    def results_dir(self) -> Path:
        return self.storage_dir / "results"

    @property
    def exports_dir(self) -> Path:
        return self.storage_dir / "exports"

    # ─── Stream ─────────────────────────────────────────────────────────────────
    DEFAULT_STREAM_FPS: int = 5
    PROCESS_EVERY_N_FRAMES: int = 5
    STREAM_JPEG_QUALITY: int = 60

    # ─── Pydantic ───────────────────────────────────────────────────────────────
    model_config = {"env_file": BASE_DIR.parent / ".env", "extra": "ignore"}


# Singleton instance reused across the app
settings = Settings()
