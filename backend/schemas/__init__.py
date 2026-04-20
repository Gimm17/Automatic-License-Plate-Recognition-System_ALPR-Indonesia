"""
backend/schemas/__init__.py
"""
from .detection import DetectionBase, DetectionCreate, DetectionResponse, DetectionListResponse
from .camera import CameraBase, CameraCreate, CameraUpdate, CameraResponse
from .vehicle import VehicleBase, VehicleCreate, VehicleUpdate, VehicleResponse

__all__ = [
    "DetectionBase","DetectionCreate","DetectionResponse","DetectionListResponse",
    "CameraBase","CameraCreate","CameraUpdate","CameraResponse",
    "VehicleBase","VehicleCreate","VehicleUpdate","VehicleResponse",
]
