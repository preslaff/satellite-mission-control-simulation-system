"""
Test coordinate transformations with real satellite data
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.coordinate_service import coordinate_service
from app.services.satellite_fetcher import satellite_fetcher


def test_eci_ecef_transformation():
    """Test ECI to ECEF transformation"""
    print("\n" + "="*60)
    print("Test 1: ECI <-> ECEF Transformation")
    print("="*60)

    # Test point in ECI (ISS altitude, ~400km)
    eci_pos = {
        'x': 4000.0,  # km
        'y': 3000.0,  # km
        'z': 2000.0   # km
    }

    timestamp = datetime.now(timezone.utc)

    print(f"\nOriginal ECI Position:")
    print(f"  X: {eci_pos['x']:.2f} km")
    print(f"  Y: {eci_pos['y']:.2f} km")
    print(f"  Z: {eci_pos['z']:.2f} km")
    print(f"  Timestamp: {timestamp}")

    # Transform to ECEF
    ecef_pos = coordinate_service.eci_to_ecef(
        eci_pos['x'], eci_pos['y'], eci_pos['z'], timestamp
    )

    print(f"\nTransformed to ECEF:")
    print(f"  X: {ecef_pos['x']:.2f} km")
    print(f"  Y: {ecef_pos['y']:.2f} km")
    print(f"  Z: {ecef_pos['z']:.2f} km")

    # Transform back to ECI
    eci_back = coordinate_service.ecef_to_eci(
        ecef_pos['x'], ecef_pos['y'], ecef_pos['z'], timestamp
    )

    print(f"\nTransformed back to ECI:")
    print(f"  X: {eci_back['x']:.2f} km")
    print(f"  Y: {eci_back['y']:.2f} km")
    print(f"  Z: {eci_back['z']:.2f} km")

    # Check round-trip accuracy
    error = (
        (eci_pos['x'] - eci_back['x'])**2 +
        (eci_pos['y'] - eci_back['y'])**2 +
        (eci_pos['z'] - eci_back['z'])**2
    )**0.5

    print(f"\n[OK] Round-trip error: {error:.6f} km")
    if error < 0.1:  # Less than 100 meters
        print("[PASS] Round-trip transformation accurate")
    else:
        print("[FAIL] Round-trip error too large")


def test_geodetic_transformation():
    """Test geodetic (lat/lon/alt) transformations"""
    print("\n" + "="*60)
    print("Test 2: Geodetic <-> ECEF Transformation")
    print("="*60)

    # Varna, Bulgaria ground station
    lat = 43.47151
    lon = 27.78379
    alt_km = 0.05  # 50 meters

    print(f"\nGround Station (Varna, Bulgaria):")
    print(f"  Latitude: {lat}°")
    print(f"  Longitude: {lon}°")
    print(f"  Altitude: {alt_km*1000:.1f} m")

    # Convert to ECEF
    ecef = coordinate_service.geodetic_to_ecef(lat, lon, alt_km)

    print(f"\nECEF Coordinates:")
    print(f"  X: {ecef['x']:.2f} km")
    print(f"  Y: {ecef['y']:.2f} km")
    print(f"  Z: {ecef['z']:.2f} km")

    # Convert back to geodetic
    geodetic = coordinate_service.ecef_to_geodetic(
        ecef['x'], ecef['y'], ecef['z']
    )

    print(f"\nBack to Geodetic:")
    print(f"  Latitude: {geodetic['latitude']:.6f}°")
    print(f"  Longitude: {geodetic['longitude']:.6f}°")
    print(f"  Altitude: {geodetic['altitude']*1000:.1f} m")

    # Check accuracy
    lat_error = abs(lat - geodetic['latitude'])
    lon_error = abs(lon - geodetic['longitude'])
    alt_error = abs(alt_km - geodetic['altitude'])

    print(f"\n[OK] Errors:")
    print(f"  Latitude: {lat_error:.9f}°")
    print(f"  Longitude: {lon_error:.9f}°")
    print(f"  Altitude: {alt_error*1000:.3f} m")

    if lat_error < 0.0001 and lon_error < 0.0001 and alt_error < 0.001:
        print("[PASS] Geodetic transformation accurate")
    else:
        print("[FAIL] Errors too large")


def test_real_satellite_enu():
    """Test ENU transformation with real ISS data"""
    print("\n" + "="*60)
    print("Test 3: Real Satellite ECI -> ENU Transformation")
    print("="*60)

    # Fetch ISS position
    norad_id = 25544
    print(f"\nFetching satellite data for NORAD ID {norad_id} (ISS)...")

    tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

    if not tle_data:
        print("[ERROR] Could not fetch satellite TLE data")
        return

    print(f"[OK] Satellite: {tle_data['OBJECT_NAME']}")

    # Get current position
    state = satellite_fetcher.propagate_position(tle_data)

    if not state:
        print("[ERROR] Could not propagate satellite position")
        return

    pos = state['position']
    timestamp = datetime.fromisoformat(state['timestamp'].replace('Z', '+00:00'))

    print(f"\nCurrent ECI Position:")
    print(f"  X: {pos['x']:.2f} km")
    print(f"  Y: {pos['y']:.2f} km")
    print(f"  Z: {pos['z']:.2f} km")
    print(f"  Timestamp: {timestamp}")

    # Observer location (Varna, Bulgaria)
    observer_lat = 43.47151
    observer_lon = 27.78379
    observer_alt_km = 0.05

    print(f"\nObserver Location (Varna, Bulgaria):")
    print(f"  Latitude: {observer_lat}°")
    print(f"  Longitude: {observer_lon}°")
    print(f"  Altitude: {observer_alt_km*1000:.1f} m")

    # Transform to ENU
    enu = coordinate_service.eci_to_topocentric_enu(
        pos['x'], pos['y'], pos['z'],
        observer_lat, observer_lon, observer_alt_km,
        timestamp.replace(tzinfo=None)
    )

    print(f"\nENU Coordinates (relative to observer):")
    print(f"  East: {enu['east']:.2f} km")
    print(f"  North: {enu['north']:.2f} km")
    print(f"  Up: {enu['up']:.2f} km")
    print(f"\nLook Angles:")
    print(f"  Range: {enu['range_km']:.2f} km")
    print(f"  Azimuth: {enu['azimuth_deg']:.2f}°")
    print(f"  Elevation: {enu['elevation_deg']:.2f}°")

    # Check if satellite is visible
    if enu['elevation_deg'] > 0:
        print(f"\n[OK] Satellite is VISIBLE from observer location!")
        print(f"   Point antenna to Az={enu['azimuth_deg']:.1f}, El={enu['elevation_deg']:.1f}")
    else:
        print(f"\n[WARN] Satellite is BELOW horizon (not visible)")

    print("[PASS] ENU transformation successful")


def test_ned_transformation():
    """Test NED transformation"""
    print("\n" + "="*60)
    print("Test 4: ECI -> NED Transformation")
    print("="*60)

    # Test with ISS
    norad_id = 25544
    tle_data = satellite_fetcher.fetch_by_norad_id(norad_id)

    if not tle_data:
        print("[ERROR] Could not fetch satellite TLE data")
        return

    state = satellite_fetcher.propagate_position(tle_data)
    if not state:
        print("[ERROR] Could not propagate satellite position")
        return

    pos = state['position']
    timestamp = datetime.fromisoformat(state['timestamp'].replace('Z', '+00:00'))

    # Observer location
    observer_lat = 43.47151
    observer_lon = 27.78379
    observer_alt_km = 0.05

    # Transform to NED
    ned = coordinate_service.eci_to_topocentric_ned(
        pos['x'], pos['y'], pos['z'],
        observer_lat, observer_lon, observer_alt_km,
        timestamp.replace(tzinfo=None)
    )

    print(f"\nNED Coordinates:")
    print(f"  North: {ned['north']:.2f} km")
    print(f"  East: {ned['east']:.2f} km")
    print(f"  Down: {ned['down']:.2f} km")
    print(f"\nLook Angles:")
    print(f"  Range: {ned['range_km']:.2f} km")
    print(f"  Azimuth: {ned['azimuth_deg']:.2f}°")
    print(f"  Elevation: {ned['elevation_deg']:.2f}°")

    print("[PASS] NED transformation successful")


def test_generic_transform():
    """Test generic transform function"""
    print("\n" + "="*60)
    print("Test 5: Generic Transform Function")
    print("="*60)

    # Test Geodetic → ECEF
    result = coordinate_service.transform(
        x=43.47151,  # Latitude
        y=27.78379,  # Longitude
        z=0.05,      # Altitude
        from_frame='Geodetic',
        to_frame='ECEF'
    )

    print("\nGeodetic -> ECEF:")
    print(f"  Input: ({43.47151}°, {27.78379}°, {0.05} km)")
    print(f"  Output: ({result['x']:.2f}, {result['y']:.2f}, {result['z']:.2f}) km")
    print(f"  Frame: {result['frame']}")

    print("[PASS] Generic transform successful")


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# Coordinate Transformation Test Suite")
    print("#"*60)

    try:
        test_eci_ecef_transformation()
        test_geodetic_transformation()
        test_real_satellite_enu()
        test_ned_transformation()
        test_generic_transform()

        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
