"""
backend/models/__init__.py
Export all ORM models so Alembic autogenerate can discover them.
"""

from .detection import Detection
from .camera import Camera
from .vehicle import Vehicle

__all__ = ["Detection", "Camera", "Vehicle"]
