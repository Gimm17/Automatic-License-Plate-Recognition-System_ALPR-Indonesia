"""
backend/database.py
SQLAlchemy engine + session factory for MySQL via PyMySQL.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from config import settings


# ─── Connection URL ──────────────────────────────────────────────────────────
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8mb4"
)

# ─── Engine ──────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # Re-check connection health before each use
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,           # Recycle connections every hour
    echo=settings.APP_DEBUG,     # Log SQL in debug mode
)

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
