"""
Satellite API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.satellite_fetcher import satellite_fetcher

router = APIRouter()


@router.get("")
async def list_satellites(
    group: str = Query(default="starlink", description="Satellite group (starlink, stations, weather, etc.)"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of satellites to return")
):
    """
    List satellites with current positions

    Args:
        group: Satellite group name
        limit: Maximum number of satellites (1-100)

    Returns:
        List of satellites with position data
    """
    try:
        satellites = satellite_fetcher.get_satellites_with_positions(group=group, limit=limit)

        return {
            "count": len(satellites),
            "group": group,
            "satellites": satellites
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching satellites: {str(e)}")


@router.get("/{norad_id}")
async def get_satellite(norad_id: int):
    """
    Get specific satellite by NORAD ID

    Args:
        norad_id: NORAD catalog number

    Returns:
        Satellite data with current position
    """
    try:
        tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

        if not tle_data:
            raise HTTPException(status_code=404, detail=f"Satellite {norad_id} not found")

        state = satellite_fetcher.propagate_position(tle_data)

        if not state:
            raise HTTPException(status_code=500, detail="Failed to calculate satellite position")

        return {
            'id': tle_data['NORAD_CAT_ID'],
            'name': tle_data['OBJECT_NAME'],
            'position': state['position'],
            'velocity': state['velocity'],
            'timestamp': state['timestamp'],
            'tle': {
                'line1': tle_data.get('TLE_LINE1', ''),
                'line2': tle_data.get('TLE_LINE2', '')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{norad_id}/orbit")
async def get_satellite_orbit(
    norad_id: int,
    duration: int = Query(default=24, ge=1, le=168, description="Orbit duration in hours"),
    step: int = Query(default=5, ge=1, le=60, description="Time step in minutes")
):
    """
    Get satellite orbit path

    Args:
        norad_id: NORAD catalog number
        duration: How many hours to propagate (1-168)
        step: Time step in minutes (1-60)

    Returns:
        List of position/velocity states over time
    """
    try:
        tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

        if not tle_data:
            raise HTTPException(status_code=404, detail=f"Satellite {norad_id} not found")

        orbit_points = satellite_fetcher.propagate_orbit(
            tle_data,
            duration_hours=duration,
            step_minutes=step
        )

        return {
            'id': tle_data['NORAD_CAT_ID'],
            'name': tle_data['OBJECT_NAME'],
            'orbit_points': orbit_points,
            'duration_hours': duration,
            'step_minutes': step
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{norad_id}/passes")
async def predict_satellite_passes(
    norad_id: int,
    lat: float = Query(..., description="Ground station latitude in degrees"),
    lon: float = Query(..., description="Ground station longitude in degrees"),
    duration: int = Query(default=24, ge=1, le=168, description="Prediction duration in hours"),
    min_elevation: float = Query(default=10.0, ge=0, le=90, description="Minimum elevation angle in degrees")
):
    """
    Predict satellite passes over a ground station

    Args:
        norad_id: NORAD catalog number
        lat: Ground station latitude (-90 to 90)
        lon: Ground station longitude (-180 to 180)
        duration: How many hours ahead to predict (1-168)
        min_elevation: Minimum elevation angle (0-90)

    Returns:
        List of predicted passes with rise/set times and max elevation
    """
    try:
        # Validate coordinates
        if lat < -90 or lat > 90:
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
        if lon < -180 or lon > 180:
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")

        tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

        if not tle_data:
            raise HTTPException(status_code=404, detail=f"Satellite {norad_id} not found")

        passes = satellite_fetcher.predict_passes(
            tle_data,
            station_lat=lat,
            station_lon=lon,
            duration_hours=duration,
            min_elevation=min_elevation
        )

        return {
            'id': tle_data['NORAD_CAT_ID'],
            'name': tle_data['OBJECT_NAME'],
            'ground_station': {
                'lat': lat,
                'lon': lon
            },
            'prediction_duration_hours': duration,
            'min_elevation': min_elevation,
            'passes': passes,
            'pass_count': len(passes)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{norad_id}/azel")
async def get_current_azel(
    norad_id: int,
    lat: float = Query(..., description="Ground station latitude in degrees"),
    lon: float = Query(..., description="Ground station longitude in degrees")
):
    """
    Get current azimuth and elevation angles for a satellite from a ground station

    Args:
        norad_id: NORAD catalog number
        lat: Ground station latitude (-90 to 90)
        lon: Ground station longitude (-180 to 180)

    Returns:
        Current azimuth, elevation, and visibility status
    """
    try:
        # Validate coordinates
        if lat < -90 or lat > 90:
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
        if lon < -180 or lon > 180:
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")

        tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

        if not tle_data:
            raise HTTPException(status_code=404, detail=f"Satellite {norad_id} not found")

        # Get current satellite position
        state = satellite_fetcher.propagate_position(tle_data)

        if not state:
            raise HTTPException(status_code=500, detail="Failed to calculate satellite position")

        # Convert satellite position to tuple for calculations
        sat_pos = (state['position']['x'], state['position']['y'], state['position']['z'])

        # Get ground station position in ECEF
        station_pos = satellite_fetcher.lat_lon_to_ecef(lat, lon)

        # Calculate azimuth and elevation
        elevation = satellite_fetcher.calculate_elevation_angle(sat_pos, station_pos)
        azimuth = satellite_fetcher.calculate_azimuth_angle(sat_pos, station_pos, lat, lon)

        # Determine if satellite is visible (elevation > 0)
        is_visible = elevation > 0

        return {
            'id': tle_data['NORAD_CAT_ID'],
            'name': tle_data['OBJECT_NAME'],
            'timestamp': state['timestamp'],
            'ground_station': {
                'lat': lat,
                'lon': lon
            },
            'azimuth': round(azimuth, 2),
            'elevation': round(elevation, 2),
            'is_visible': is_visible,
            'position': state['position'],
            'velocity': state['velocity']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/groups/available")
async def list_available_groups():
    """List available satellite groups"""
    return {
        "groups": list(satellite_fetcher.GROUPS.keys()),
        "descriptions": {
            "starlink": "Starlink constellation satellites",
            "stations": "Space stations (ISS, etc.)",
            "weather": "Weather satellites",
            "active": "All active satellites",
            "gps": "GPS constellation"
        }
    }

