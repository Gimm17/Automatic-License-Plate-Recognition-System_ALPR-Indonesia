"""
backend/main.py
FastAPI application entry point for ALPR Indonesia.

Startup:
  - Initializes YOLOService and OCRService ONCE (heavyweight, ~5-15s)
  - Initializes StreamService
  - Serves static files from storage/results/
  - Registers all routers under /api with CORS
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import Base, engine, check_db_connection
from models import Detection, Camera, Vehicle  # import so alembic/Base can see them
from routers import (
    detection_router,
    cameras_router,
    vehicles_router,
    stats_router,
    export_router,
    ws_router,
    stream_api_router,
)
from services.yolo_service import YOLOService
from services.ocr_service import OCRService
from services.stream_service import StreamService
from services.detection_worker import DetectionWorker
from security import require_api_key

logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan (replaces @app.on_event) ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App startup: initialize ML services and ensure storage dirs exist.
    App shutdown: (placeholder for cleanup).
    """
    logger.info("=== ALPR Indonesia starting up ===")

    # Ensure storage directories exist
    for d in [settings.temp_dir, settings.results_dir, settings.exports_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Create DB tables (no-op if already exist; use Alembic for migrations in prod)
    if check_db_connection():
        logger.info("Database connection OK — ensuring tables exist")
        Base.metadata.create_all(bind=engine)
    else:
        logger.warning("Database NOT reachable at startup — some endpoints will fail")

    # Initialize ML services (singleton, shared via app.state)
    # Wrapped in try/except so backend starts even if ultralytics/paddleocr are not yet installed
    try:
        logger.info("Initializing YOLOService …")
        app.state.yolo = YOLOService(
            model_path=settings.yolo_model_full_path,
            conf_threshold=settings.YOLO_CONFIDENCE,
        )

        logger.info("Initializing OCRService …")
        app.state.ocr = OCRService(language=settings.OCR_LANGUAGE)

        logger.info("Initializing StreamService …")
        app.state.stream = StreamService(
            yolo_service=app.state.yolo,
            ocr_service=app.state.ocr,
        )

        # Initialize background detection worker. It starts only when enabled.
        logger.info("Initializing DetectionWorker")
        worker = DetectionWorker(
            yolo_service=app.state.yolo,
            ocr_service=app.state.ocr,
        )
        app.state.detection_worker = worker

        if settings.ENABLE_DETECTION_WORKER:
            # Load active cameras from DB and start processing them.
            from database import SessionLocal
            from models.camera import Camera as CameraModel
            db = SessionLocal()
            try:
                active_cams = db.query(CameraModel).filter(CameraModel.is_active == True).all()
                if active_cams:
                    worker.start_all(active_cams)
                    logger.info(f"DetectionWorker started for {len(active_cams)} camera(s)")
                else:
                    logger.info("No active cameras found; DetectionWorker idle")
            finally:
                db.close()
        else:
            logger.info("DetectionWorker disabled by ENABLE_DETECTION_WORKER=false")

        logger.info("=== All services ready ===")
    except Exception as e:
        logger.warning(
            f"⚠️  ML services could not be initialized: {e}\n"
            "  → Detection/stream endpoints will return 503.\n"
            "  → Install ultralytics & paddleocr to enable ML features."
        )
        app.state.yolo   = None
        app.state.ocr    = None
        app.state.stream = None
        app.state.detection_worker = None

    yield

    # Shutdown: stop background detection
    worker = getattr(app.state, 'detection_worker', None)
    if worker:
        worker.stop_all()
    logger.info("=== ALPR Indonesia shutting down ===")


# ─── App instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="ALPR Indonesia API",
    description="Automatic License Plate Recognition System for Indonesian vehicles",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "data": None, "message": str(exc.detail)},
    )

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files — serve annotated images ────────────────────────────────────
# Access: GET /storage/results/xxxxxx_annotated.jpg
_storage = settings.storage_dir
_storage.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(_storage)), name="storage")

_static = settings.static_dir
if (_static / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(_static / "assets")), name="assets")

# ─── Include routers ──────────────────────────────────────────────────────────
_protected_api = [Depends(require_api_key)]
app.include_router(detection_router, dependencies=_protected_api)
app.include_router(cameras_router, dependencies=_protected_api)
app.include_router(vehicles_router, dependencies=_protected_api)
app.include_router(stats_router, dependencies=_protected_api)
app.include_router(export_router, dependencies=_protected_api)
app.include_router(stream_api_router, dependencies=_protected_api)
app.include_router(ws_router)   # WebSocket — no prefix (path = /ws/stream/{id})


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Quick liveness probe.
    Returns DB status, OCR availability, and model load status.
    """
    db_ok  = check_db_connection()
    ocr_ok = getattr(app.state, "ocr", None) is not None and \
              app.state.ocr.is_available()

    return {
        "success": True,
        "data": {
            "status":      "ok",
            "database":    "connected" if db_ok else "unavailable",
            "ocr_engine":  "ready" if ocr_ok else "unavailable",
            "yolo_model":  "loaded" if getattr(app.state, "yolo", None) is not None else "not_loaded",
            "worker":      "enabled" if settings.ENABLE_DETECTION_WORKER else "disabled",
            "version":     "1.0.0",
        },
        "message": "ALPR Indonesia API is running",
    }


# ─── Dev entry point ──────────────────────────────────────────────────────────
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Serve the Vue SPA build without shadowing API, WS, docs, or storage."""
    blocked_prefixes = ("api", "ws", "storage", "docs", "redoc", "openapi.json")
    if full_path.startswith(blocked_prefixes):
        raise HTTPException(status_code=404, detail="Not found")

    static_file = settings.static_dir / full_path
    if static_file.is_file():
        return FileResponse(static_file)

    index_file = settings.static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="SPA build not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_DEBUG,
        log_level="debug" if settings.APP_DEBUG else "info",
    )
