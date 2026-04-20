"""
backend/routers/vehicles.py
Fase 2 — Vehicle lookup database endpoints.

Endpoints:
  GET    /api/vehicles             — List/search vehicles
  POST   /api/vehicles             — Add vehicle to lookup DB
  GET    /api/vehicles/lookup/{plate} — Quick lookup by plate text
  GET    /api/vehicles/{id}        — Get vehicle detail by ID
  PUT    /api/vehicles/{id}        — Update vehicle record
  DELETE /api/vehicles/{id}        — Remove vehicle from DB
  POST   /api/vehicles/{id}/flag   — Flag a vehicle as watchlist
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models.vehicle import Vehicle
from models.detection import Detection
from schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from services.plate_validator import clean_ocr_text
from utils.response import success_response, error_response, paginated_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


# ─── GET /api/vehicles ────────────────────────────────────────────────────────
@router.get("")
async def list_vehicles(
    page:   int           = 1,
    limit:  int           = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Return paginated list of vehicles, with optional full-text search.

    Query params:
        search: Search by plate_text, owner_name, or brand
        status: Filter by vehicle status (normal | watchlist | stolen | expired)
    """
    query = db.query(Vehicle)

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Vehicle.plate_text.ilike(term),
                Vehicle.owner_name.ilike(term),
                Vehicle.brand.ilike(term),
            )
        )
    if status:
        query = query.filter(Vehicle.status == status)

    total  = query.count()
    offset = (page - 1) * limit
    items  = query.order_by(Vehicle.plate_text).offset(offset).limit(limit).all()

    serialized = [VehicleResponse.model_validate(v).model_dump() for v in items]
    return paginated_response(serialized, total, page, limit)


# ─── POST /api/vehicles ───────────────────────────────────────────────────────
@router.post("")
async def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)):
    """
    Add a vehicle to the lookup database.

    Body:
        plate_text:   Plate number (unique, required)
        owner_name:   Registered owner
        vehicle_type: Car / Truck / Motorcycle
        brand:        Vehicle brand
        color:        Vehicle color
        year:         Year of manufacture
        status:       normal | watchlist | stolen | expired
        notes:        Freeform notes
    """
    plate = clean_ocr_text(payload.plate_text)

    existing = db.query(Vehicle).filter(Vehicle.plate_text == plate).first()
    if existing:
        return error_response(
            f"Vehicle with plate '{plate}' already exists. Use PUT to update.", code=409
        )

    vehicle = Vehicle(**{**payload.model_dump(), "plate_text": plate})
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    logger.info(f"Vehicle added: plate={plate} status={vehicle.status}")
    return success_response(
        VehicleResponse.model_validate(vehicle).model_dump(),
        "Vehicle registered successfully",
    )


# ─── GET /api/vehicles/lookup/{plate} ────────────────────────────────────────
@router.get("/lookup/{plate}")
async def lookup_vehicle_by_plate(plate: str, db: Session = Depends(get_db)):
    """
    Quick lookup: find a vehicle by its plate number.

    This is the endpoint called during ALPR pipeline to check watchlists.
    Returns 404 with `found: false` if not registered.
    """
    clean = clean_ocr_text(plate)
    vehicle = db.query(Vehicle).filter(Vehicle.plate_text == clean).first()

    if not vehicle:
        return success_response(
            {"found": False, "plate": clean, "vehicle": None},
            "Vehicle not in database",
        )

    return success_response(
        {
            "found":   True,
            "plate":   clean,
            "vehicle": VehicleResponse.model_validate(vehicle).model_dump(),
        },
        f"Vehicle found — status: {vehicle.status}",
    )


# ─── GET /api/vehicles/{id} ───────────────────────────────────────────────────
@router.get("/{vehicle_id}")
async def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get full vehicle detail including detection history count."""
    vehicle = _get_or_404(vehicle_id, db)

    # Count how many times this plate has been detected
    detection_count = (
        db.query(Detection)
        .filter(Detection.plate_text == vehicle.plate_text)
        .count()
    )

    data = VehicleResponse.model_validate(vehicle).model_dump()
    data["detection_count"] = detection_count

    return success_response(data)


# ─── PUT /api/vehicles/{id} ───────────────────────────────────────────────────
@router.put("/{vehicle_id}")
async def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
):
    """Update a vehicle record. Only provided fields are changed."""
    vehicle = _get_or_404(vehicle_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    logger.info(f"Vehicle updated: id={vehicle_id} fields={list(update_data.keys())}")
    return success_response(
        VehicleResponse.model_validate(vehicle).model_dump(),
        "Vehicle updated successfully",
    )


# ─── DELETE /api/vehicles/{id} ────────────────────────────────────────────────
@router.delete("/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Permanently remove a vehicle from the lookup database."""
    vehicle = _get_or_404(vehicle_id, db)
    plate = vehicle.plate_text

    db.delete(vehicle)
    db.commit()

    logger.info(f"Vehicle deleted: id={vehicle_id} plate={plate}")
    return success_response(None, f"Vehicle '{plate}' removed from database")


# ─── POST /api/vehicles/{id}/flag ─────────────────────────────────────────────
@router.post("/{vehicle_id}/flag")
async def flag_vehicle(
    vehicle_id: int,
    status: str = "watchlist",
    notes:  Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Quickly change a vehicle's status to watchlist (or any other status).

    Query params:
        status: Target status — watchlist | stolen | expired | normal
        notes:  Reason for flagging
    """
    valid_statuses = {"normal", "watchlist", "stolen", "expired"}
    if status not in valid_statuses:
        return error_response(
            f"Invalid status '{status}'. Must be one of: {valid_statuses}", code=422
        )

    vehicle = _get_or_404(vehicle_id, db)
    old_status = vehicle.status

    vehicle.status = status
    if notes:
        vehicle.notes = notes

    db.commit()
    db.refresh(vehicle)

    logger.warning(
        f"Vehicle flagged: plate={vehicle.plate_text} "
        f"{old_status} → {status}"
    )
    return success_response(
        VehicleResponse.model_validate(vehicle).model_dump(),
        f"Vehicle status changed to '{status}'",
    )


# ─── Helper ───────────────────────────────────────────────────────────────────
def _get_or_404(vehicle_id: int, db: Session) -> Vehicle:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle
