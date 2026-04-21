"""
backend/database.py
SQLAlchemy engine + session factory.
- Production: MySQL via PyMySQL (configured in .env)
- Local dev fallback: SQLite when MySQL is unreachable
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from config import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

# ─── Connection URL ──────────────────────────────────────────────────────────
MYSQL_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8mb4"
)
SQLITE_URL = f"sqlite:///{BASE_DIR / 'storage' / 'alpr_dev.db'}"

def _create_engine_with_fallback():
    """Try MySQL first; fall back to SQLite for local development."""
    try:
        eng = create_engine(
            MYSQL_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            echo=settings.APP_DEBUG,
        )
        # Test connection
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Connected to MySQL database")
        return eng
    except Exception as e:
        logger.warning(f"⚠️  MySQL unavailable ({e}) — falling back to SQLite")
        # Ensure storage dir exists
        (BASE_DIR / "storage").mkdir(parents=True, exist_ok=True)
        return create_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False},
            echo=settings.APP_DEBUG,
        )

# ─── Engine ──────────────────────────────────────────────────────────────────
engine = _create_engine_with_fallback()

# ─── Session Factory ─────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# ─── Base Model Class ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── FastAPI Dependency ───────────────────────────────────────────────────────
def get_db():
    """
    Yield a database session for use as a FastAPI dependency.
    Guarantees the session is closed after the request.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Context Manager (for scripts / startup) ─────────────────────────────────
@contextmanager
def get_db_context():
    """Context manager for use outside FastAPI dependency injection."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """Ping the database. Returns True if reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
