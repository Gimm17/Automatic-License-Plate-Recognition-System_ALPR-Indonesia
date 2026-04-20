"""
backend/schemas/vehicle.py
Pydantic schemas for Vehicle model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VehicleBase(BaseModel):
    plate_text:   str   = Field(..., max_length=20)
    owner_name:   Optional[str] = None
    vehicle_type: Optional[str] = None
    brand:        Optional[str] = None
    color:        Optional[str] = None
    year:         Optional[int] = Field(None, ge=1900, le=2100)
    status:       str           = "normal"
    notes:        Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    owner_name:   Optional[str] = None
    vehicle_type: Optional[str] = None
    brand:        Optional[str] = None
    color:        Optional[str] = None
    year:         Optional[int] = Field(None, ge=1900, le=2100)
    status:       Optional[str] = None
    notes:        Optional[str] = None


class VehicleResponse(VehicleBase):
    id:         int
    created_at: datetime

    model_config = {"from_attributes": True}
