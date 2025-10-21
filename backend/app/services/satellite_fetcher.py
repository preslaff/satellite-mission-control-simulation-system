"""
Satellite Data Fetcher Service
Fetches TLE data from CelesTrak and propagates satellite positions using SGP4
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np
from sgp4.api import Satrec, jday


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
        self.cache_duration = timedelta(hours=1)

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

        if group in self.cache:
            if datetime.now() - self.cache_timestamp[group] < self.cache_duration:
                satellites = self.cache[group]
                return satellites[:limit] if limit else satellites

        try:
            url = f"{self.BASE_URL}gp.php?GROUP={group_key}&FORMAT=tle"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

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

            self.cache[group] = satellites
            self.cache_timestamp[group] = datetime.now()

            return satellites[:limit] if limit else satellites

        except Exception as e:
            print(f"Error fetching satellites: {e}")
            return []

    def fetch_by_norad_id(self, norad_id: int) -> Optional[Dict]:
        """Fetch specific satellite by NORAD catalog number"""
        try:
            url = f"{self.BASE_URL}gp.php?CATNR={norad_id}&FORMAT=tle"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

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

        except Exception as e:
            print(f"Error fetching satellite {norad_id}: {e}")
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


satellite_fetcher = SatelliteFetcher()
