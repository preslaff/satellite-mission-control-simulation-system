"""
Coordinate System Transformation Service

Provides high-accuracy transformations between:
- ECI (Earth-Centered Inertial) - J2000/GCRS
- ECEF (Earth-Centered Earth-Fixed) - WGS84/ITRS
- Topocentric (Observer-relative) - ENU (East-North-Up) and NED (North-East-Down)

Uses skyfield for high-precision calculations.
"""

import numpy as np
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional
from skyfield.api import load, wgs84, utc, Distance
from skyfield.positionlib import Geocentric
from skyfield.framelib import itrs
from skyfield.units import Angle
import math


class CoordinateTransformService:
    """Service for transforming coordinates between different reference frames"""

    def __init__(self):
        """Initialize coordinate transformation service with skyfield timescale"""
        self.ts = load.timescale()
        self.earth_radius_km = 6371.0  # Mean Earth radius in km
        # Load planets for creating positions
        self.planets = load('de421.bsp')
        self.earth = self.planets['earth']

    def eci_to_ecef(
        self,
        x: float,
        y: float,
        z: float,
        timestamp: datetime
    ) -> Dict[str, float]:
        """
        Convert ECI (J2000/GCRS) coordinates to ECEF (Earth-Fixed/ITRS) coordinates

        Args:
            x, y, z: Position in ECI frame (km)
            timestamp: Time of observation (UTC)

        Returns:
            Dictionary with ECEF coordinates {x, y, z} in km
        """
        # Ensure timestamp is timezone-aware (UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=utc)

        # Convert datetime to skyfield time
        t = self.ts.from_datetime(timestamp)

        # Create a geocentric position in GCRS (ECI J2000 equivalent)
        # Skyfield uses Distance objects for coordinates
        distance_au = [x / 149597870.7, y / 149597870.7, z / 149597870.7]  # Convert km to AU

        # Create Geocentric position in GCRS frame
        position = Geocentric(distance_au, t=t)

        # Transform to ITRS (Earth-fixed frame)
        itrs_position = position.frame_xyz(itrs)

        return {
            'x': itrs_position.km[0],
            'y': itrs_position.km[1],
            'z': itrs_position.km[2],
            'frame': 'ECEF',
            'timestamp': timestamp.isoformat()
        }

    def ecef_to_eci(
        self,
        x: float,
        y: float,
        z: float,
        timestamp: datetime
    ) -> Dict[str, float]:
        """
        Convert ECEF (Earth-Fixed/ITRS) coordinates to ECI (J2000/GCRS) coordinates

        Args:
            x, y, z: Position in ECEF frame (km)
            timestamp: Time of observation (UTC)

        Returns:
            Dictionary with ECI coordinates {x, y, z} in km
        """
        # Ensure timestamp is timezone-aware (UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=utc)

        # Convert datetime to skyfield time
        t = self.ts.from_datetime(timestamp)

        # Create Distance objects for ITRS coordinates
        from skyfield.positionlib import build_position

        # Convert km to AU for skyfield
        distance_au = [x / 149597870.7, y / 149597870.7, z / 149597870.7]

        # Create position in ITRS frame and transform to GCRS
        # We need to use the reverse transformation
        # Create a Geocentric position and specify it's in ITRS frame
        itrs_position = Geocentric(distance_au, t=t)

        # To get GCRS from ITRS, we need to apply the inverse rotation
        # Skyfield's frame_xyz gives us coordinates IN a frame FROM GCRS
        # So we need to work backwards

        # Alternative approach: use geodetic intermediate
        lat_lon_alt = self.ecef_to_geodetic(x, y, z)

        # Create geographic location
        location = wgs84.latlon(
            lat_lon_alt['latitude'],
            lat_lon_alt['longitude'],
            elevation_m=lat_lon_alt['altitude'] * 1000  # Convert km to meters
        )

        # Get position in GCRS (ECI)
        gcrs_position = location.at(t)

        # Get GCRS coordinates
        gcrs_xyz = gcrs_position.position.km

        return {
            'x': gcrs_xyz[0],
            'y': gcrs_xyz[1],
            'z': gcrs_xyz[2],
            'frame': 'ECI',
            'timestamp': timestamp.isoformat()
        }

    def ecef_to_geodetic(
        self,
        x: float,
        y: float,
        z: float
    ) -> Dict[str, float]:
        """
        Convert ECEF coordinates to geodetic (lat, lon, altitude)

        Args:
            x, y, z: Position in ECEF frame (km)

        Returns:
            Dictionary with latitude (deg), longitude (deg), altitude (km)
        """
        # Convert km to AU for skyfield
        distance_au = [x / 149597870.7, y / 149597870.7, z / 149597870.7]

        # Create a time (doesn't matter for ECEF->Geodetic conversion)
        t = self.ts.now()

        # Create a Geocentric position in ITRS frame
        # Since Geocentric creates positions in GCRS by default, we need to work around this
        # The easiest approach is to use the mathematical conversion directly

        # WGS84 ellipsoid parameters
        a = 6378.137  # semi-major axis in km
        b = 6356.752314245  # semi-minor axis in km
        e_sq = 1 - (b**2 / a**2)  # eccentricity squared

        # Calculate longitude
        lon_rad = math.atan2(y, x)

        # Calculate latitude (iterative method)
        p = math.sqrt(x**2 + y**2)
        lat_rad = math.atan2(z, p * (1 - e_sq))

        # Iterate to refine latitude
        for _ in range(5):
            N = a / math.sqrt(1 - e_sq * math.sin(lat_rad)**2)
            lat_rad = math.atan2(z + e_sq * N * math.sin(lat_rad), p)

        # Calculate altitude
        N = a / math.sqrt(1 - e_sq * math.sin(lat_rad)**2)
        alt_km = p / math.cos(lat_rad) - N

        return {
            'latitude': math.degrees(lat_rad),
            'longitude': math.degrees(lon_rad),
            'altitude': alt_km,
            'frame': 'Geodetic'
        }

    def geodetic_to_ecef(
        self,
        latitude: float,
        longitude: float,
        altitude_km: float = 0.0
    ) -> Dict[str, float]:
        """
        Convert geodetic (lat, lon, altitude) to ECEF coordinates

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            altitude_km: Altitude above WGS84 ellipsoid in km

        Returns:
            Dictionary with ECEF coordinates {x, y, z} in km
        """
        # Create geographic location
        location = wgs84.latlon(
            latitude,
            longitude,
            elevation_m=altitude_km * 1000  # Convert km to meters
        )

        # Get ITRS position at arbitrary time (doesn't matter for static point)
        t = self.ts.now()
        position = location.at(t)

        # Get ITRS coordinates (ECEF)
        itrs_xyz = position.frame_xyz(itrs).km

        return {
            'x': itrs_xyz[0],
            'y': itrs_xyz[1],
            'z': itrs_xyz[2],
            'frame': 'ECEF'
        }

    def eci_to_topocentric_enu(
        self,
        sat_x: float,
        sat_y: float,
        sat_z: float,
        observer_lat: float,
        observer_lon: float,
        observer_alt_km: float,
        timestamp: datetime
    ) -> Dict[str, float]:
        """
        Convert ECI satellite position to topocentric ENU (East-North-Up)
        relative to an observer

        Args:
            sat_x, sat_y, sat_z: Satellite position in ECI (km)
            observer_lat: Observer latitude (degrees)
            observer_lon: Observer longitude (degrees)
            observer_alt_km: Observer altitude (km)
            timestamp: Time of observation

        Returns:
            Dictionary with ENU coordinates {east, north, up} in km,
            plus range, azimuth, elevation
        """
        # Ensure timestamp is timezone-aware (UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=utc)

        # Convert datetime to skyfield time
        t = self.ts.from_datetime(timestamp)

        # Create observer location
        observer = wgs84.latlon(
            observer_lat,
            observer_lon,
            elevation_m=observer_alt_km * 1000  # Convert km to meters
        )

        # Create satellite position in GCRS (ECI)
        distance_au = [sat_x / 149597870.7, sat_y / 149597870.7, sat_z / 149597870.7]
        sat_position = Geocentric(distance_au, t=t)

        # Calculate topocentric position (satellite - observer)
        # We need to convert to skyfield's position format
        # Create an observer position at Earth center
        from skyfield.positionlib import build_position

        # Alternative approach: use ECEF for the calculation
        # First convert satellite ECI to ECEF
        sat_ecef = self.eci_to_ecef(sat_x, sat_y, sat_z, timestamp)

        # Convert observer location to ECEF
        obs_ecef = self.geodetic_to_ecef(observer_lat, observer_lon, observer_alt_km)

        # Calculate satellite position relative to observer in ECEF
        dx = sat_ecef['x'] - obs_ecef['x']
        dy = sat_ecef['y'] - obs_ecef['y']
        dz = sat_ecef['z'] - obs_ecef['z']

        # Convert to ENU using rotation matrix
        lat_rad = math.radians(observer_lat)
        lon_rad = math.radians(observer_lon)

        # ENU rotation matrix
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)

        east = -sin_lon * dx + cos_lon * dy
        north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
        up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz

        # Calculate range, azimuth, elevation
        range_km = math.sqrt(east**2 + north**2 + up**2)
        azimuth_deg = math.degrees(math.atan2(east, north)) % 360
        elevation_deg = math.degrees(math.asin(up / range_km)) if range_km > 0 else 0

        return {
            'east': east,
            'north': north,
            'up': up,
            'range_km': range_km,
            'azimuth_deg': azimuth_deg,
            'elevation_deg': elevation_deg,
            'frame': 'ENU',
            'observer': {
                'latitude': observer_lat,
                'longitude': observer_lon,
                'altitude_km': observer_alt_km
            },
            'timestamp': timestamp.isoformat()
        }

    def eci_to_topocentric_ned(
        self,
        sat_x: float,
        sat_y: float,
        sat_z: float,
        observer_lat: float,
        observer_lon: float,
        observer_alt_km: float,
        timestamp: datetime
    ) -> Dict[str, float]:
        """
        Convert ECI satellite position to topocentric NED (North-East-Down)

        NED is commonly used in aviation and aerospace applications.
        """
        # Get ENU first
        enu = self.eci_to_topocentric_enu(
            sat_x, sat_y, sat_z,
            observer_lat, observer_lon, observer_alt_km,
            timestamp
        )

        # Convert ENU to NED (swap axes and negate down)
        north = enu['north']
        east = enu['east']
        down = -enu['up']

        range_km = enu['range_km']
        azimuth_deg = enu['azimuth_deg']
        elevation_deg = enu['elevation_deg']

        return {
            'north': north,
            'east': east,
            'down': down,
            'range_km': range_km,
            'azimuth_deg': azimuth_deg,
            'elevation_deg': elevation_deg,
            'frame': 'NED',
            'observer': {
                'latitude': observer_lat,
                'longitude': observer_lon,
                'altitude_km': observer_alt_km
            },
            'timestamp': timestamp.isoformat()
        }

    def transform(
        self,
        x: float,
        y: float,
        z: float,
        from_frame: str,
        to_frame: str,
        timestamp: Optional[datetime] = None,
        observer_lat: Optional[float] = None,
        observer_lon: Optional[float] = None,
        observer_alt_km: Optional[float] = 0.0
    ) -> Dict:
        """
        Generic transformation between any coordinate frames

        Args:
            x, y, z: Coordinates in source frame
            from_frame: Source frame ('ECI', 'ECEF', 'Geodetic')
            to_frame: Target frame ('ECI', 'ECEF', 'Geodetic', 'ENU', 'NED')
            timestamp: Time of observation (required for ECI/ECEF conversions)
            observer_lat, observer_lon, observer_alt_km: Required for topocentric frames

        Returns:
            Dictionary with transformed coordinates
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=utc)

        from_frame = from_frame.upper()
        to_frame = to_frame.upper()

        # Direct transformations
        if from_frame == 'ECI' and to_frame == 'ECEF':
            return self.eci_to_ecef(x, y, z, timestamp)

        elif from_frame == 'ECEF' and to_frame == 'ECI':
            return self.ecef_to_eci(x, y, z, timestamp)

        elif from_frame == 'ECEF' and to_frame == 'GEODETIC':
            return self.ecef_to_geodetic(x, y, z)

        elif from_frame == 'GEODETIC' and to_frame == 'ECEF':
            # For geodetic, x=lat, y=lon, z=altitude
            return self.geodetic_to_ecef(x, y, z)

        elif from_frame == 'ECI' and to_frame == 'ENU':
            if observer_lat is None or observer_lon is None:
                raise ValueError("Observer location required for ENU frame")
            return self.eci_to_topocentric_enu(
                x, y, z, observer_lat, observer_lon, observer_alt_km, timestamp
            )

        elif from_frame == 'ECI' and to_frame == 'NED':
            if observer_lat is None or observer_lon is None:
                raise ValueError("Observer location required for NED frame")
            return self.eci_to_topocentric_ned(
                x, y, z, observer_lat, observer_lon, observer_alt_km, timestamp
            )

        # Chain transformations for unsupported direct conversions
        elif from_frame == 'ECEF' and to_frame in ['ENU', 'NED']:
            # ECEF -> ECI -> ENU/NED
            eci = self.ecef_to_eci(x, y, z, timestamp)
            if to_frame == 'ENU':
                return self.eci_to_topocentric_enu(
                    eci['x'], eci['y'], eci['z'],
                    observer_lat, observer_lon, observer_alt_km, timestamp
                )
            else:  # NED
                return self.eci_to_topocentric_ned(
                    eci['x'], eci['y'], eci['z'],
                    observer_lat, observer_lon, observer_alt_km, timestamp
                )

        else:
            raise ValueError(
                f"Unsupported transformation: {from_frame} -> {to_frame}. "
                f"Supported: ECI, ECEF, Geodetic, ENU, NED"
            )


# Global coordinate service instance
coordinate_service = CoordinateTransformService()
