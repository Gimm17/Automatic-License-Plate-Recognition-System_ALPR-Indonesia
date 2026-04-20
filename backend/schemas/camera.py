"""
backend/schemas/camera.py
Pydantic schemas for Camera model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CameraBase(BaseModel):
    name:       str         = Field(..., max_length=100)
    location:   Optional[str] = Field(None, max_length=200)
    rtsp_url:   Optional[str] = None
    is_active:  bool        = True
    stream_fps: int         = Field(5, ge=1, le=60)


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name:       Optional[str] = None
    location:   Optional[str] = None
    rtsp_url:   Optional[str] = None
    is_active:  Optional[bool] = None
    stream_fps: Optional[int] = Field(None, ge=1, le=60)


class CameraResponse(CameraBase):
    id:         int
    created_at: datetime

    model_config = {"from_attributes": True}
