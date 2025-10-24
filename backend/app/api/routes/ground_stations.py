"""
Ground Station API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services import db_service


router = APIRouter()


# Pydantic models for request/response
class GroundStationCreate(BaseModel):
    name: str = Field(..., description="Ground station name")
    code: Optional[str] = Field(None, description="Station code (e.g., 'NYC' for New York)")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    altitude: float = Field(default=0.0, ge=0, description="Altitude in meters above sea level")
    min_elevation: float = Field(default=10.0, ge=0, le=90, description="Minimum elevation angle for visibility (degrees)")


class GroundStationResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    latitude: float
    longitude: float
    altitude: float
    min_elevation: float
    is_active: bool

    class Config:
        from_attributes = True


@router.post("", response_model=GroundStationResponse, status_code=201)
async def create_ground_station(
    station: GroundStationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ground station

    Args:
        station: Ground station data
        db: Database session

    Returns:
        Created ground station
    """
    try:
        db_station = db_service.create_ground_station(
            db=db,
            name=station.name,
            latitude=station.latitude,
            longitude=station.longitude,
            altitude=station.altitude,
            code=station.code,
            min_elevation=station.min_elevation
        )

        return db_station

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ground station: {str(e)}")


@router.get("", response_model=List[GroundStationResponse])
async def list_ground_stations(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List all ground stations

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of ground stations
    """
    try:
        stations = db_service.get_ground_stations(db, skip=skip, limit=limit)
        return stations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ground stations: {str(e)}")


@router.get("/{station_id}", response_model=GroundStationResponse)
async def get_ground_station(
    station_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific ground station by ID

    Args:
        station_id: Ground station database ID
        db: Database session

    Returns:
        Ground station data
    """
    try:
        station = db_service.get_ground_station(db, station_id)

        if not station:
            raise HTTPException(status_code=404, detail=f"Ground station {station_id} not found")

        return station

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.put("/{station_id}", response_model=GroundStationResponse)
async def update_ground_station(
    station_id: int,
    station_update: GroundStationCreate,
    db: Session = Depends(get_db)
):
    """
    Update ground station

    Args:
        station_id: Ground station database ID
        station_update: Updated ground station data
        db: Database session

    Returns:
        Updated ground station
    """
    try:
        db_station = db_service.get_ground_station(db, station_id)

        if not db_station:
            raise HTTPException(status_code=404, detail=f"Ground station {station_id} not found")

        # Update fields
        db_station.name = station_update.name
        db_station.code = station_update.code
        db_station.latitude = station_update.latitude
        db_station.longitude = station_update.longitude
        db_station.altitude = station_update.altitude
        db_station.min_elevation = station_update.min_elevation

        db.commit()
        db.refresh(db_station)

        return db_station

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ground station: {str(e)}")


@router.delete("/{station_id}", status_code=204)
async def delete_ground_station(
    station_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete ground station (soft delete - sets is_active=False)

    Args:
        station_id: Ground station database ID
        db: Database session

    Returns:
        No content
    """
    try:
        db_station = db_service.get_ground_station(db, station_id)

        if not db_station:
            raise HTTPException(status_code=404, detail=f"Ground station {station_id} not found")

        db_station.is_active = False
        db.commit()

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting ground station: {str(e)}")
