"""
Coordinate Transformation API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

from app.services.coordinate_service import coordinate_service
from app.services.satellite_fetcher import satellite_fetcher


router = APIRouter()


# Pydantic models for request/response
class CoordinateTransformRequest(BaseModel):
    x: float = Field(..., description="X coordinate in source frame")
    y: float = Field(..., description="Y coordinate in source frame")
    z: float = Field(..., description="Z coordinate in source frame")
    from_frame: Literal['ECI', 'ECEF', 'Geodetic'] = Field(..., description="Source coordinate frame")
    to_frame: Literal['ECI', 'ECEF', 'Geodetic', 'ENU', 'NED'] = Field(..., description="Target coordinate frame")
    timestamp: Optional[datetime] = Field(None, description="Time of observation (UTC)")
    observer_lat: Optional[float] = Field(None, ge=-90, le=90, description="Observer latitude (degrees)")
    observer_lon: Optional[float] = Field(None, ge=-180, le=180, description="Observer longitude (degrees)")
    observer_alt_km: Optional[float] = Field(0.0, description="Observer altitude (km)")


class SatelliteCoordinateRequest(BaseModel):
    frame: Literal['ECI', 'ECEF', 'Geodetic', 'ENU', 'NED'] = Field(..., description="Desired coordinate frame")
    timestamp: Optional[datetime] = Field(None, description="Time for position calculation (default: now)")
    observer_lat: Optional[float] = Field(None, ge=-90, le=90, description="Observer latitude for topocentric frames")
    observer_lon: Optional[float] = Field(None, ge=-180, le=180, description="Observer longitude for topocentric frames")
    observer_alt_km: Optional[float] = Field(0.0, description="Observer altitude for topocentric frames")


@router.post("/transform")
async def transform_coordinates(request: CoordinateTransformRequest):
    """
    Transform coordinates between different reference frames

    Supported frames:
    - **ECI**: Earth-Centered Inertial (J2000)
    - **ECEF**: Earth-Centered Earth-Fixed (WGS84)
    - **Geodetic**: Latitude, Longitude, Altitude
    - **ENU**: East-North-Up (topocentric, requires observer location)
    - **NED**: North-East-Down (topocentric, requires observer location)

    Args:
        request: Transformation request with source coordinates and frames

    Returns:
        Transformed coordinates in target frame
    """
    try:
        # Validate observer location for topocentric frames
        if request.to_frame in ['ENU', 'NED']:
            if request.observer_lat is None or request.observer_lon is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Observer location (observer_lat, observer_lon) required for {request.to_frame} frame"
                )

        # Perform transformation
        result = coordinate_service.transform(
            x=request.x,
            y=request.y,
            z=request.z,
            from_frame=request.from_frame,
            to_frame=request.to_frame,
            timestamp=request.timestamp,
            observer_lat=request.observer_lat,
            observer_lon=request.observer_lon,
            observer_alt_km=request.observer_alt_km
        )

        return {
            "source": {
                "x": request.x,
                "y": request.y,
                "z": request.z,
                "frame": request.from_frame
            },
            "target": result,
            "transformation": f"{request.from_frame} → {request.to_frame}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transformation error: {str(e)}")


@router.get("/satellite/{norad_id}")
async def get_satellite_coordinates(
    norad_id: int,
    frame: Literal['ECI', 'ECEF', 'Geodetic', 'ENU', 'NED'] = Query(
        default='ECI',
        description="Coordinate frame for satellite position"
    ),
    observer_lat: Optional[float] = Query(
        None,
        ge=-90,
        le=90,
        description="Observer latitude for topocentric frames"
    ),
    observer_lon: Optional[float] = Query(
        None,
        ge=-180,
        le=180,
        description="Observer longitude for topocentric frames"
    ),
    observer_alt_km: Optional[float] = Query(
        0.0,
        description="Observer altitude in km"
    )
):
    """
    Get satellite position in specified coordinate frame

    Fetches current satellite position and transforms to requested frame.

    Args:
        norad_id: NORAD catalog number
        frame: Desired coordinate frame
        observer_lat: Observer latitude (required for ENU/NED)
        observer_lon: Observer longitude (required for ENU/NED)
        observer_alt_km: Observer altitude

    Returns:
        Satellite position in requested coordinate frame
    """
    try:
        # Fetch satellite TLE
        tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

        if not tle_data:
            raise HTTPException(
                status_code=404,
                detail=f"Satellite {norad_id} not found"
            )

        # Get current position in ECI
        state = satellite_fetcher.propagate_position(tle_data)

        if not state:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate satellite position"
            )

        # Extract position
        pos = state['position']
        vel = state['velocity']
        timestamp_str = state['timestamp']

        # Parse timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        # If already in ECI and no transformation needed
        if frame == 'ECI':
            return {
                'satellite': {
                    'norad_id': norad_id,
                    'name': tle_data['OBJECT_NAME']
                },
                'position': pos,
                'velocity': vel,
                'frame': 'ECI',
                'timestamp': timestamp_str
            }

        # Transform to requested frame
        # Validate observer location for topocentric frames
        if frame in ['ENU', 'NED']:
            if observer_lat is None or observer_lon is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Observer location required for {frame} frame"
                )

        # Perform transformation
        transformed = coordinate_service.transform(
            x=pos['x'],
            y=pos['y'],
            z=pos['z'],
            from_frame='ECI',
            to_frame=frame,
            timestamp=timestamp.replace(tzinfo=None),
            observer_lat=observer_lat,
            observer_lon=observer_lon,
            observer_alt_km=observer_alt_km
        )

        return {
            'satellite': {
                'norad_id': norad_id,
                'name': tle_data['OBJECT_NAME']
            },
            'coordinates': transformed,
            'velocity_eci': vel,  # Velocity stays in ECI for now
            'timestamp': timestamp_str
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/frames")
async def list_coordinate_frames():
    """
    List available coordinate frames and their descriptions

    Returns information about all supported coordinate reference frames.
    """
    return {
        "frames": {
            "ECI": {
                "name": "Earth-Centered Inertial",
                "description": "J2000 inertial reference frame, fixed relative to distant stars",
                "use_case": "Satellite orbit calculations, space navigation",
                "axes": {
                    "x": "Vernal equinox direction",
                    "y": "90° east in equatorial plane",
                    "z": "North celestial pole"
                }
            },
            "ECEF": {
                "name": "Earth-Centered Earth-Fixed",
                "description": "WGS84 frame rotating with Earth",
                "use_case": "Ground station positions, GPS",
                "axes": {
                    "x": "Intersection of equator and prime meridian",
                    "y": "90° east",
                    "z": "North pole"
                }
            },
            "Geodetic": {
                "name": "Geodetic Coordinates",
                "description": "Latitude, longitude, and altitude on WGS84 ellipsoid",
                "use_case": "Geographic positioning, maps",
                "coordinates": {
                    "x": "Latitude (degrees, -90 to 90)",
                    "y": "Longitude (degrees, -180 to 180)",
                    "z": "Altitude (km above WGS84)"
                }
            },
            "ENU": {
                "name": "East-North-Up (Topocentric)",
                "description": "Local tangent plane at observer location",
                "use_case": "Radar tracking, antenna pointing",
                "axes": {
                    "east": "Local east direction",
                    "north": "Local north direction",
                    "up": "Local vertical (away from Earth)"
                },
                "note": "Requires observer location"
            },
            "NED": {
                "name": "North-East-Down (Topocentric)",
                "description": "Aviation/aerospace reference frame",
                "use_case": "Aircraft navigation, UAVs",
                "axes": {
                    "north": "Local north direction",
                    "east": "Local east direction",
                    "down": "Local vertical (toward Earth)"
                },
                "note": "Requires observer location"
            }
        },
        "transformations": {
            "direct": [
                "ECI ↔ ECEF",
                "ECEF ↔ Geodetic",
                "ECI → ENU",
                "ECI → NED"
            ],
            "chained": [
                "ECEF → ENU (via ECI)",
                "ECEF → NED (via ECI)",
                "Geodetic → ECI (via ECEF)"
            ]
        }
    }


@router.get("/examples")
async def get_transformation_examples():
    """
    Get example transformations with sample data

    Provides ready-to-use examples for common transformation scenarios.
    """
    return {
        "examples": [
            {
                "title": "ISS Position from ECI to Geodetic",
                "description": "Convert ISS orbital position to latitude/longitude",
                "request": {
                    "x": 4000.0,
                    "y": 3000.0,
                    "z": 2000.0,
                    "from_frame": "ECI",
                    "to_frame": "ECEF"
                },
                "note": "Then use ECEF → Geodetic for lat/lon"
            },
            {
                "title": "Ground Station to Satellite in ENU",
                "description": "Calculate satellite position relative to ground station",
                "endpoint": "/coordinates/satellite/25544?frame=ENU&observer_lat=43.47&observer_lon=27.78",
                "note": "Returns azimuth, elevation, and range for antenna pointing"
            },
            {
                "title": "Transform Geodetic to ECEF",
                "description": "Convert lat/lon/alt to Cartesian coordinates",
                "request": {
                    "x": 43.47151,  # Latitude
                    "y": 27.78379,  # Longitude
                    "z": 0.05,      # Altitude in km
                    "from_frame": "Geodetic",
                    "to_frame": "ECEF"
                }
            }
        ]
    }
