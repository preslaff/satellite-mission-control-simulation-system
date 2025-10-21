"""
Satellite API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.satellite_fetcher import satellite_fetcher

router = APIRouter()


@router.get("/")
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
