"""
Database service layer for CRUD operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.satellite import Satellite
from app.models.telemetry import Telemetry
from app.models.ground_station import GroundStation
from app.models.satellite_pass import SatellitePass


# Satellite CRUD operations

def create_satellite(
    db: Session,
    norad_id: int,
    name: str,
    tle_line1: str,
    tle_line2: str,
    satellite_group: Optional[str] = None,
    satellite_type: Optional[str] = None,
) -> Satellite:
    """
    Create a new satellite record

    Args:
        db: Database session
        norad_id: NORAD catalog ID
        name: Satellite name
        tle_line1: TLE line 1
        tle_line2: TLE line 2
        satellite_group: Satellite group (starlink, stations, etc.)
        satellite_type: Satellite type (LEO, MEO, GEO, etc.)

    Returns:
        Created Satellite object
    """
    db_satellite = Satellite(
        norad_id=norad_id,
        name=name,
        tle_line1=tle_line1,
        tle_line2=tle_line2,
        satellite_group=satellite_group,
        satellite_type=satellite_type,
    )
    db.add(db_satellite)
    db.commit()
    db.refresh(db_satellite)
    return db_satellite


def get_satellite_by_norad_id(db: Session, norad_id: int) -> Optional[Satellite]:
    """Get satellite by NORAD ID"""
    return db.query(Satellite).filter(Satellite.norad_id == norad_id).first()


def get_satellite_by_id(db: Session, satellite_id: int) -> Optional[Satellite]:
    """Get satellite by database ID"""
    return db.query(Satellite).filter(Satellite.id == satellite_id).first()


def get_satellites(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    group: Optional[str] = None,
    is_active: bool = True,
) -> List[Satellite]:
    """
    Get list of satellites with optional filters

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        group: Filter by satellite group
        is_active: Filter by active status

    Returns:
        List of Satellite objects
    """
    query = db.query(Satellite).filter(Satellite.is_active == is_active)

    if group:
        query = query.filter(Satellite.satellite_group == group)

    return query.offset(skip).limit(limit).all()


def update_satellite_tle(
    db: Session, satellite_id: int, tle_line1: str, tle_line2: str
) -> Optional[Satellite]:
    """Update satellite TLE data"""
    satellite = get_satellite_by_id(db, satellite_id)
    if satellite:
        satellite.tle_line1 = tle_line1
        satellite.tle_line2 = tle_line2
        satellite.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(satellite)
    return satellite


def delete_satellite(db: Session, satellite_id: int) -> bool:
    """Soft delete a satellite (set is_active=False)"""
    satellite = get_satellite_by_id(db, satellite_id)
    if satellite:
        satellite.is_active = False
        db.commit()
        return True
    return False


# Telemetry CRUD operations

def create_telemetry(
    db: Session,
    satellite_id: int,
    timestamp: datetime,
    position_x: float,
    position_y: float,
    position_z: float,
    velocity_x: float,
    velocity_y: float,
    velocity_z: float,
    altitude_km: Optional[float] = None,
    velocity_km_s: Optional[float] = None,
) -> Telemetry:
    """Create a new telemetry record"""
    db_telemetry = Telemetry(
        satellite_id=satellite_id,
        timestamp=timestamp,
        position_x=position_x,
        position_y=position_y,
        position_z=position_z,
        velocity_x=velocity_x,
        velocity_y=velocity_y,
        velocity_z=velocity_z,
        altitude_km=altitude_km,
        velocity_km_s=velocity_km_s,
    )
    db.add(db_telemetry)
    db.commit()
    db.refresh(db_telemetry)
    return db_telemetry


def get_latest_telemetry(db: Session, satellite_id: int) -> Optional[Telemetry]:
    """Get the most recent telemetry for a satellite"""
    return (
        db.query(Telemetry)
        .filter(Telemetry.satellite_id == satellite_id)
        .order_by(Telemetry.timestamp.desc())
        .first()
    )


def get_telemetry_history(
    db: Session,
    satellite_id: int,
    start_time: datetime,
    end_time: datetime,
    limit: int = 1000,
) -> List[Telemetry]:
    """Get telemetry history for a satellite within a time range"""
    return (
        db.query(Telemetry)
        .filter(
            Telemetry.satellite_id == satellite_id,
            Telemetry.timestamp >= start_time,
            Telemetry.timestamp <= end_time,
        )
        .order_by(Telemetry.timestamp)
        .limit(limit)
        .all()
    )


# Ground Station CRUD operations

def create_ground_station(
    db: Session,
    name: str,
    latitude: float,
    longitude: float,
    altitude: float = 0.0,
    code: Optional[str] = None,
    min_elevation: float = 10.0,
) -> GroundStation:
    """Create a new ground station"""
    db_station = GroundStation(
        name=name,
        code=code,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        min_elevation=min_elevation,
    )
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station


def get_ground_station(db: Session, station_id: int) -> Optional[GroundStation]:
    """Get ground station by ID"""
    return db.query(GroundStation).filter(GroundStation.id == station_id).first()


def get_ground_stations(
    db: Session, skip: int = 0, limit: int = 100
) -> List[GroundStation]:
    """Get list of ground stations"""
    return db.query(GroundStation).offset(skip).limit(limit).all()


# Satellite Pass CRUD operations

def create_satellite_pass(
    db: Session,
    satellite_id: int,
    ground_station_id: int,
    rise_time: datetime,
    set_time: datetime,
    max_elevation_time: datetime,
    max_elevation: float,
    rise_azimuth: float,
    set_azimuth: float,
    duration_seconds: float,
) -> SatellitePass:
    """Create a new satellite pass record"""
    db_pass = SatellitePass(
        satellite_id=satellite_id,
        ground_station_id=ground_station_id,
        rise_time=rise_time,
        set_time=set_time,
        max_elevation_time=max_elevation_time,
        max_elevation=max_elevation,
        rise_azimuth=rise_azimuth,
        set_azimuth=set_azimuth,
        duration_seconds=duration_seconds,
    )
    db.add(db_pass)
    db.commit()
    db.refresh(db_pass)
    return db_pass


def get_upcoming_passes(
    db: Session,
    satellite_id: int,
    ground_station_id: int,
    start_time: datetime,
    limit: int = 10,
) -> List[SatellitePass]:
    """Get upcoming passes for a satellite over a ground station"""
    return (
        db.query(SatellitePass)
        .filter(
            SatellitePass.satellite_id == satellite_id,
            SatellitePass.ground_station_id == ground_station_id,
            SatellitePass.rise_time >= start_time,
        )
        .order_by(SatellitePass.rise_time)
        .limit(limit)
        .all()
    )


def get_passes_in_range(
    db: Session,
    start_time: datetime,
    end_time: datetime,
    ground_station_id: Optional[int] = None,
) -> List[SatellitePass]:
    """Get all satellite passes within a time range"""
    query = db.query(SatellitePass).filter(
        SatellitePass.rise_time >= start_time, SatellitePass.set_time <= end_time
    )

    if ground_station_id:
        query = query.filter(SatellitePass.ground_station_id == ground_station_id)

    return query.order_by(SatellitePass.rise_time).all()
