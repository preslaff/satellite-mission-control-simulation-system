"""
Satellite Data Fetcher Service
Fetches TLE data from CelesTrak and propagates satellite positions using SGP4
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np
from sgp4.api import Satrec, jday
import math
import json
import os
from pathlib import Path
import time


class SatelliteFetcher:
    """Fetch and process satellite data from CelesTrak"""

    BASE_URL = "https://celestrak.org/NORAD/elements/"

    GROUPS = {
        'starlink': 'starlink',
        'stations': 'stations',
        'weather': 'weather',
        'active': 'active',
        'gps': 'gps-ops',
    }

    def __init__(self):
        self.cache = {}
        self.cache_timestamp = {}
        self.cache_duration = timedelta(hours=2)  # Match CelesTrak update frequency
        self.max_retries = 3  # Max retry attempts per CelesTrak best practices
        self.retry_delay = 2  # Seconds between retries

        # Setup persistent cache directory
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load cached data from disk
        self._load_cache_from_disk()

    def _load_cache_from_disk(self):
        """Load cached TLE data from disk"""
        for group in self.GROUPS.keys():
            cache_file = self.cache_dir / f"{group}_tle.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                        self.cache[group] = cache_data['satellites']
                        self.cache_timestamp[group] = datetime.fromisoformat(cache_data['timestamp'])
                        print(f"Loaded {len(self.cache[group])} satellites from cache for group '{group}'")
                except Exception as e:
                    print(f"Error loading cache for {group}: {e}")

    def _save_cache_to_disk(self, group: str):
        """Save cached TLE data to disk"""
        if group in self.cache:
            try:
                cache_file = self.cache_dir / f"{group}_tle.json"
                cache_data = {
                    'satellites': self.cache[group],
                    'timestamp': self.cache_timestamp[group].isoformat()
                }
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                print(f"Saved {len(self.cache[group])} satellites to cache for group '{group}'")
            except Exception as e:
                print(f"Error saving cache for {group}: {e}")

    def fetch_group(self, group: str = 'starlink', limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch satellite group from CelesTrak

        Args:
            group: Satellite group name
            limit: Maximum number of satellites to return

        Returns:
            List of satellite TLE data dictionaries
        """
        group_key = self.GROUPS.get(group, group)

        # Return fresh cache if available
        if group in self.cache:
            if datetime.now() - self.cache_timestamp[group] < self.cache_duration:
                print(f"Using fresh cache for group '{group}' ({len(self.cache[group])} satellites)")
                satellites = self.cache[group]
                return satellites[:limit] if limit else satellites

        # Try to fetch from CelesTrak with retry logic
        url = f"{self.BASE_URL}gp.php?GROUP={group_key}&FORMAT=tle"

        for attempt in range(self.max_retries):
            try:
                print(f"Fetching TLE data from CelesTrak for group '{group}' (attempt {attempt + 1}/{self.max_retries})...")
                response = requests.get(url, timeout=30)

                # Check HTTP status code explicitly
                if response.status_code == 200:
                    # Success - process the data
                    tle_text = response.text
                    lines = tle_text.strip().split('\n')

                    satellites = []
                    for i in range(0, len(lines), 3):
                        if i + 2 < len(lines):
                            satellites.append({
                                'OBJECT_NAME': lines[i].strip(),
                                'TLE_LINE1': lines[i + 1].strip(),
                                'TLE_LINE2': lines[i + 2].strip(),
                                'NORAD_CAT_ID': int(lines[i + 2][2:7])
                            })

                    # Update memory and disk cache
                    self.cache[group] = satellites
                    self.cache_timestamp[group] = datetime.now()
                    self._save_cache_to_disk(group)

                    print(f"Successfully fetched {len(satellites)} satellites for group '{group}'")
                    return satellites[:limit] if limit else satellites

                elif response.status_code == 403:
                    # IP blocked by CelesTrak - stop retrying immediately
                    print(f"WARNING: CelesTrak returned HTTP 403 Forbidden - Your IP may be blocked")
                    print(f"WARNING: This could be due to exceeding rate limits (>10,000 errors/day)")
                    print(f"WARNING: Block will auto-clear in 2 hours. Falling back to cached data.")
                    break  # Don't retry on 403

                else:
                    # Other HTTP error
                    print(f"CelesTrak returned HTTP {response.status_code}: {response.reason}")
                    if attempt < self.max_retries - 1:
                        print(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)

            except requests.exceptions.Timeout:
                print(f"Request timeout after 30 seconds")
                if attempt < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
                if attempt < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

            except Exception as e:
                print(f"Unexpected error fetching satellites from CelesTrak: {e}")
                if attempt < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

        # All retries failed - fallback to stale cache if available
        print(f"All {self.max_retries} retry attempts failed for group '{group}'")
        if group in self.cache:
            age_hours = (datetime.now() - self.cache_timestamp[group]).total_seconds() / 3600
            print(f"Falling back to cached data for group '{group}' (age: {age_hours:.1f} hours)")
            satellites = self.cache[group]
            return satellites[:limit] if limit else satellites

        print(f"No cached data available for group '{group}'")
        return []

    def fetch_by_norad_id(self, norad_id: int) -> Optional[Dict]:
        """
        Fetch specific satellite by NORAD catalog number

        First searches in existing group caches (stations, starlink, weather, gps)
        to avoid unnecessary CelesTrak API calls. Only fetches from CelesTrak
        if the satellite is not found in any cached group.
        """
        # STEP 1: Search in existing group caches first
        for group, satellites in self.cache.items():
            for sat in satellites:
                if sat.get('NORAD_CAT_ID') == norad_id:
                    # Found in cache - return immediately without CelesTrak call
                    # cache_age = (datetime.now() - self.cache_timestamp.get(group, datetime.min)).total_seconds() / 3600
                    # print(f"Using cached satellite {norad_id} from group '{group}' (age: {cache_age:.1f} hours)")
                    return sat

        # STEP 2: Not found in any cache - fetch from CelesTrak as fallback
        print(f"Satellite {norad_id} not in cache, fetching from CelesTrak...")
        url = f"{self.BASE_URL}gp.php?CATNR={norad_id}&FORMAT=tle"

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    tle_text = response.text
                    lines = tle_text.strip().split('\n')

                    if len(lines) >= 3:
                        return {
                            'OBJECT_NAME': lines[0].strip(),
                            'TLE_LINE1': lines[1].strip(),
                            'TLE_LINE2': lines[2].strip(),
                            'NORAD_CAT_ID': int(lines[2][2:7])
                        }
                    return None

                elif response.status_code == 403:
                    print(f"WARNING: CelesTrak blocked (HTTP 403) - Cannot fetch satellite {norad_id}")
                    break

                else:
                    print(f"CelesTrak returned HTTP {response.status_code} for satellite {norad_id}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)

            except Exception as e:
                print(f"Error fetching satellite {norad_id}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        return None

    def create_satrec(self, tle_data: Dict) -> Optional[Satrec]:
        """
        Create SGP4 satellite object from TLE data

        Args:
            tle_data: TLE data dictionary from CelesTrak

        Returns:
            Satrec object or None if error
        """
        try:
            line1 = tle_data['TLE_LINE1']
            line2 = tle_data['TLE_LINE2']

            sat = Satrec.twoline2rv(line1, line2)
            return sat

        except Exception as e:
            print(f"Error creating Satrec: {e}")
            return None

    def propagate_position(self, tle_data: Dict, dt: Optional[datetime] = None) -> Optional[Dict]:
        """
        Propagate satellite position at given time

        Args:
            tle_data: TLE data dictionary
            dt: Datetime to propagate to (defaults to now)

        Returns:
            Dictionary with position and velocity, or None if error
        """
        if dt is None:
            dt = datetime.utcnow()

        sat = self.create_satrec(tle_data)
        if not sat:
            return None

        try:
            jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

            error_code, position, velocity = sat.sgp4(jd, fr)

            if error_code != 0:
                print(f"SGP4 error code: {error_code}")
                return None

            return {
                'position': {
                    'x': position[0],
                    'y': position[1],
                    'z': position[2]
                },
                'velocity': {
                    'vx': velocity[0],
                    'vy': velocity[1],
                    'vz': velocity[2]
                },
                'timestamp': dt.isoformat()
            }

        except Exception as e:
            print(f"Error propagating position: {e}")
            return None

    def get_satellites_with_positions(self, group: str = 'starlink', limit: int = 10) -> List[Dict]:
        """
        Fetch satellites and calculate their current positions

        Args:
            group: Satellite group
            limit: Maximum number of satellites

        Returns:
            List of satellites with positions
        """
        satellites = self.fetch_group(group, limit=limit)
        result = []

        for sat_data in satellites:
            state = self.propagate_position(sat_data)
            if state:
                result.append({
                    'id': sat_data['NORAD_CAT_ID'],
                    'name': sat_data['OBJECT_NAME'],
                    'position': state['position'],
                    'velocity': state['velocity'],
                    'timestamp': state['timestamp'],
                    'tle': {
                        'line1': sat_data.get('TLE_LINE1', ''),
                        'line2': sat_data.get('TLE_LINE2', '')
                    }
                })

        return result

    def propagate_orbit(self, tle_data: Dict, duration_hours: int = 24,
                       step_minutes: int = 5) -> List[Dict]:
        """
        Propagate complete orbit over time

        Args:
            tle_data: TLE data dictionary
            duration_hours: How many hours to propagate
            step_minutes: Time step in minutes

        Returns:
            List of position/velocity states over time
        """
        sat = self.create_satrec(tle_data)
        if not sat:
            return []

        start_time = datetime.utcnow()
        num_steps = int(duration_hours * 60 / step_minutes)

        orbit_points = []

        for i in range(num_steps):
            dt = start_time + timedelta(minutes=step_minutes * i)
            jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

            error_code, position, velocity = sat.sgp4(jd, fr)

            if error_code == 0:
                orbit_points.append({
                    'position': {
                        'x': position[0],
                        'y': position[1],
                        'z': position[2]
                    },
                    'velocity': {
                        'vx': velocity[0],
                        'vy': velocity[1],
                        'vz': velocity[2]
                    },
                    'timestamp': dt.isoformat()
                })

        return orbit_points

    def lat_lon_to_ecef(self, lat_deg: float, lon_deg: float, alt_km: float = 0.0) -> tuple:
        """
        Convert latitude/longitude to ECEF coordinates

        Args:
            lat_deg: Latitude in degrees
            lon_deg: Longitude in degrees
            alt_km: Altitude in km (default 0)

        Returns:
            Tuple of (x, y, z) in kilometers
        """
        EARTH_RADIUS_KM = 6378.137  # WGS84 equatorial radius

        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)

        x = (EARTH_RADIUS_KM + alt_km) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (EARTH_RADIUS_KM + alt_km) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (EARTH_RADIUS_KM + alt_km) * math.sin(lat_rad)

        return (x, y, z)

    def calculate_elevation_angle(self, sat_pos: tuple, station_pos: tuple) -> float:
        """
        Calculate elevation angle from ground station to satellite

        Args:
            sat_pos: Satellite position (x, y, z) in km
            station_pos: Ground station position (x, y, z) in km

        Returns:
            Elevation angle in degrees
        """
        # Vector from station to satellite
        dx = sat_pos[0] - station_pos[0]
        dy = sat_pos[1] - station_pos[1]
        dz = sat_pos[2] - station_pos[2]

        # Distance
        distance = math.sqrt(dx**2 + dy**2 + dz**2)

        # Up direction (radial from Earth center through station)
        station_dist = math.sqrt(station_pos[0]**2 + station_pos[1]**2 + station_pos[2]**2)
        up_x = station_pos[0] / station_dist
        up_y = station_pos[1] / station_dist
        up_z = station_pos[2] / station_dist

        # Dot product of station-to-sat vector with up direction
        dot_product = (dx * up_x + dy * up_y + dz * up_z)

        # Calculate elevation angle
        elevation_rad = math.asin(dot_product / distance)
        elevation_deg = math.degrees(elevation_rad)

        return elevation_deg

    def calculate_azimuth_angle(self, sat_pos: tuple, station_pos: tuple, station_lat: float, station_lon: float) -> float:
        """
        Calculate azimuth angle from ground station to satellite

        Args:
            sat_pos: Satellite position (x, y, z) in km (ECEF)
            station_pos: Ground station position (x, y, z) in km (ECEF)
            station_lat: Ground station latitude in degrees
            station_lon: Ground station longitude in degrees

        Returns:
            Azimuth angle in degrees (0° = North, 90° = East, 180° = South, 270° = West)
        """
        # Vector from station to satellite
        dx = sat_pos[0] - station_pos[0]
        dy = sat_pos[1] - station_pos[1]
        dz = sat_pos[2] - station_pos[2]

        # Convert station lat/lon to radians
        lat_rad = math.radians(station_lat)
        lon_rad = math.radians(station_lon)

        # Local ENU (East-North-Up) basis vectors at station
        # East vector
        east_x = -math.sin(lon_rad)
        east_y = math.cos(lon_rad)
        east_z = 0

        # North vector
        north_x = -math.sin(lat_rad) * math.cos(lon_rad)
        north_y = -math.sin(lat_rad) * math.sin(lon_rad)
        north_z = math.cos(lat_rad)

        # Project satellite direction onto local horizontal plane (ENU)
        east_component = dx * east_x + dy * east_y + dz * east_z
        north_component = dx * north_x + dy * north_y + dz * north_z

        # Calculate azimuth from north (clockwise)
        azimuth_rad = math.atan2(east_component, north_component)
        azimuth_deg = math.degrees(azimuth_rad)

        # Normalize to 0-360 degrees
        if azimuth_deg < 0:
            azimuth_deg += 360

        return azimuth_deg

    def predict_passes(self, tle_data: Dict, station_lat: float, station_lon: float,
                      duration_hours: int = 24, min_elevation: float = 10.0) -> List[Dict]:
        """
        Predict satellite passes over a ground station

        Args:
            tle_data: TLE data dictionary
            station_lat: Ground station latitude in degrees
            station_lon: Ground station longitude in degrees
            duration_hours: How many hours ahead to predict (default 24)
            min_elevation: Minimum elevation angle in degrees (default 10)

        Returns:
            List of pass dictionaries with rise_time, set_time, max_elevation, etc.
        """
        sat = self.create_satrec(tle_data)
        if not sat:
            return []

        # Ground station position in ECEF
        station_pos = self.lat_lon_to_ecef(station_lat, station_lon)

        # Time parameters
        start_time = datetime.utcnow()
        step_seconds = 10  # Check every 10 seconds for accuracy
        num_steps = int(duration_hours * 3600 / step_seconds)

        passes = []
        current_pass = None

        for i in range(num_steps):
            dt = start_time + timedelta(seconds=step_seconds * i)
            jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

            error_code, position, velocity = sat.sgp4(jd, fr)

            if error_code != 0:
                continue

            # Calculate elevation angle
            elevation = self.calculate_elevation_angle(position, station_pos)

            # Detect pass start (rising above minimum elevation)
            if elevation >= min_elevation and current_pass is None:
                azimuth = self.calculate_azimuth_angle(position, station_pos, station_lat, station_lon)
                current_pass = {
                    'rise_time': dt,
                    'rise_azimuth': azimuth,
                    'max_elevation': elevation,
                    'max_elevation_time': dt,
                    'elevations': [(dt, elevation, position)]  # Store position for later
                }

            # Update current pass
            elif current_pass is not None:
                if elevation >= min_elevation:
                    # Still in pass
                    current_pass['elevations'].append((dt, elevation, position))

                    # Update max elevation
                    if elevation > current_pass['max_elevation']:
                        current_pass['max_elevation'] = elevation
                        current_pass['max_elevation_time'] = dt
                else:
                    # Pass ended (dropped below minimum elevation)
                    last_dt, last_elev, last_pos = current_pass['elevations'][-1]
                    set_azimuth = self.calculate_azimuth_angle(last_pos, station_pos, station_lat, station_lon)

                    current_pass['set_time'] = last_dt
                    current_pass['set_azimuth'] = set_azimuth
                    current_pass['duration_seconds'] = (current_pass['set_time'] - current_pass['rise_time']).total_seconds()

                    # Clean up elevations list (not needed in final output)
                    del current_pass['elevations']

                    passes.append(current_pass)
                    current_pass = None

        # Handle pass that extends beyond prediction window
        if current_pass is not None:
            last_dt, last_elev, last_pos = current_pass['elevations'][-1]
            set_azimuth = self.calculate_azimuth_angle(last_pos, station_pos, station_lat, station_lon)

            current_pass['set_time'] = last_dt
            current_pass['set_azimuth'] = set_azimuth
            current_pass['duration_seconds'] = (current_pass['set_time'] - current_pass['rise_time']).total_seconds()
            del current_pass['elevations']
            passes.append(current_pass)

        # Convert datetime objects to ISO format strings
        for pass_data in passes:
            pass_data['rise_time'] = pass_data['rise_time'].isoformat()
            pass_data['set_time'] = pass_data['set_time'].isoformat()
            pass_data['max_elevation_time'] = pass_data['max_elevation_time'].isoformat()

        return passes


satellite_fetcher = SatelliteFetcher()
