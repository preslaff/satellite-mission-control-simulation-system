"""
Telemetry API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services import db_service
from app.services.satellite_fetcher import satellite_fetcher


router = APIRouter()


# Pydantic models for request/response
class TelemetryCreate(BaseModel):
    satellite_id: int = Field(..., description="Database ID of the satellite")
    timestamp: datetime = Field(..., description="Timestamp of the telemetry data")
    position_x: float = Field(..., description="X position in ECI coordinates (km)")
    position_y: float = Field(..., description="Y position in ECI coordinates (km)")
    position_z: float = Field(..., description="Z position in ECI coordinates (km)")
    velocity_x: float = Field(..., description="X velocity in ECI coordinates (km/s)")
    velocity_y: float = Field(..., description="Y velocity in ECI coordinates (km/s)")
    velocity_z: float = Field(..., description="Z velocity in ECI coordinates (km/s)")
    altitude_km: Optional[float] = Field(None, description="Altitude above Earth surface (km)")
    velocity_km_s: Optional[float] = Field(None, description="Total velocity magnitude (km/s)")


class TelemetryResponse(BaseModel):
    id: int
    satellite_id: int
    timestamp: datetime
    position_x: float
    position_y: float
    position_z: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    altitude_km: Optional[float]
    velocity_km_s: Optional[float]

    class Config:
        from_attributes = True


class TelemetryBatchCreate(BaseModel):
    satellite_id: int
    records: List[TelemetryCreate]


@router.post("", response_model=TelemetryResponse, status_code=201)
async def create_telemetry(
    telemetry: TelemetryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new telemetry record

    Args:
        telemetry: Telemetry data
        db: Database session

    Returns:
        Created telemetry record
    """
    try:
        db_telemetry = db_service.create_telemetry(
            db=db,
            satellite_id=telemetry.satellite_id,
            timestamp=telemetry.timestamp,
            position_x=telemetry.position_x,
            position_y=telemetry.position_y,
            position_z=telemetry.position_z,
            velocity_x=telemetry.velocity_x,
            velocity_y=telemetry.velocity_y,
            velocity_z=telemetry.velocity_z,
            altitude_km=telemetry.altitude_km,
            velocity_km_s=telemetry.velocity_km_s
        )

        return db_telemetry

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating telemetry: {str(e)}")


@router.post("/batch", status_code=201)
async def create_telemetry_batch(
    batch: TelemetryBatchCreate,
    db: Session = Depends(get_db)
):
    """
    Create multiple telemetry records in batch (more efficient)

    Args:
        batch: Batch of telemetry records
        db: Database session

    Returns:
        Count of created records
    """
    try:
        created_count = 0

        for record in batch.records:
            db_service.create_telemetry(
                db=db,
                satellite_id=batch.satellite_id,
                timestamp=record.timestamp,
                position_x=record.position_x,
                position_y=record.position_y,
                position_z=record.position_z,
                velocity_x=record.velocity_x,
                velocity_y=record.velocity_y,
                velocity_z=record.velocity_z,
                altitude_km=record.altitude_km,
                velocity_km_s=record.velocity_km_s
            )
            created_count += 1

        return {
            "satellite_id": batch.satellite_id,
            "created_count": created_count,
            "message": f"Successfully created {created_count} telemetry records"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating telemetry batch: {str(e)}")


@router.get("/{satellite_id}/current", response_model=Optional[TelemetryResponse])
async def get_current_telemetry(
    satellite_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the most recent telemetry for a satellite

    Args:
        satellite_id: Database ID of the satellite
        db: Database session

    Returns:
        Latest telemetry record or None
    """
    try:
        telemetry = db_service.get_latest_telemetry(db, satellite_id)

        if not telemetry:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry found for satellite {satellite_id}"
            )

        return telemetry

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{satellite_id}/history", response_model=List[TelemetryResponse])
async def get_telemetry_history(
    satellite_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Number of hours of history to retrieve"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    Get historical telemetry for a satellite

    Args:
        satellite_id: Database ID of the satellite
        hours: Number of hours of history (1-168)
        limit: Maximum number of records (1-10000)
        db: Database session

    Returns:
        List of telemetry records
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        telemetry = db_service.get_telemetry_history(
            db=db,
            satellite_id=satellite_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        return telemetry

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/capture/{norad_id}", response_model=TelemetryResponse, status_code=201)
async def capture_current_telemetry(
    norad_id: int,
    db: Session = Depends(get_db)
):
    """
    Capture current satellite position and save to database

    This endpoint fetches the current satellite state from TLE data
    and saves it as a telemetry record.

    Args:
        norad_id: NORAD catalog number
        db: Database session

    Returns:
        Created telemetry record
    """
    try:
        # Get satellite from database
        satellite = db_service.get_satellite_by_norad_id(db, norad_id)

        if not satellite:
            raise HTTPException(
                status_code=404,
                detail=f"Satellite with NORAD ID {norad_id} not found in database. "
                       f"Please sync satellites first using sync_satellites_to_db.py"
            )

        # Fetch current TLE data
        tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

        if not tle_data:
            raise HTTPException(
                status_code=404,
                detail=f"TLE data for satellite {norad_id} not found"
            )

        # Propagate current position
        state = satellite_fetcher.propagate_position(tle_data)

        if not state:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate satellite position"
            )

        # Calculate altitude and velocity magnitude
        pos = state['position']
        vel = state['velocity']

        # Calculate distance from Earth center
        distance_km = (pos['x']**2 + pos['y']**2 + pos['z']**2)**0.5
        # Earth mean radius: 6371 km
        altitude_km = distance_km - 6371.0

        # Calculate velocity magnitude
        velocity_km_s = (vel['vx']**2 + vel['vy']**2 + vel['vz']**2)**0.5

        # Save to database
        db_telemetry = db_service.create_telemetry(
            db=db,
            satellite_id=satellite.id,
            timestamp=datetime.fromisoformat(state['timestamp'].replace('Z', '+00:00')),
            position_x=pos['x'],
            position_y=pos['y'],
            position_z=pos['z'],
            velocity_x=vel['vx'],
            velocity_y=vel['vy'],
            velocity_z=vel['vz'],
            altitude_km=altitude_km,
            velocity_km_s=velocity_km_s
        )

        return db_telemetry

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error capturing telemetry: {str(e)}")


@router.get("/stats/{satellite_id}")
async def get_telemetry_stats(
    satellite_id: int,
    db: Session = Depends(get_db)
):
    """
    Get telemetry statistics for a satellite

    Args:
        satellite_id: Database ID of the satellite
        db: Database session

    Returns:
        Statistics about telemetry data
    """
    try:
        from sqlalchemy import func
        from app.models.telemetry import Telemetry

        # Get count and time range
        stats = db.query(
            func.count(Telemetry.id).label('count'),
            func.min(Telemetry.timestamp).label('first_record'),
            func.max(Telemetry.timestamp).label('last_record'),
            func.avg(Telemetry.altitude_km).label('avg_altitude'),
            func.avg(Telemetry.velocity_km_s).label('avg_velocity')
        ).filter(Telemetry.satellite_id == satellite_id).first()

        if stats.count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry found for satellite {satellite_id}"
            )

        return {
            "satellite_id": satellite_id,
            "total_records": stats.count,
            "first_record": stats.first_record,
            "last_record": stats.last_record,
            "avg_altitude_km": round(stats.avg_altitude, 2) if stats.avg_altitude else None,
            "avg_velocity_km_s": round(stats.avg_velocity, 2) if stats.avg_velocity else None,
            "time_span_hours": (
                (stats.last_record - stats.first_record).total_seconds() / 3600
                if stats.first_record and stats.last_record else 0
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
