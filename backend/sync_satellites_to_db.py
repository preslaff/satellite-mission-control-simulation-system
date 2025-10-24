"""
Sync cached satellites from satellite_fetcher to PostgreSQL database

This script populates the database with satellites from the cached TLE data.
Run this after starting the backend to populate the satellites table.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal, check_db_connection
from app.services.satellite_fetcher import satellite_fetcher
from app.services.db_service import (
    create_satellite,
    get_satellite_by_norad_id,
    update_satellite_tle,
)


def sync_satellites_to_db(groups: list = None):
    """
    Sync satellites from cache to database

    Args:
        groups: List of satellite groups to sync. If None, syncs all groups.
    """

    # Check database connection
    if not check_db_connection():
        print("[ERROR] Database connection failed! Check your DATABASE_URL in .env")
        return False

    print("[OK] Database connection successful")

    # Default groups to sync
    if groups is None:
        groups = ['stations', 'starlink', 'weather', 'gps', 'active']

    db = SessionLocal()

    try:
        total_added = 0
        total_updated = 0
        total_errors = 0

        for group in groups:
            print(f"\n[GROUP] Processing group: {group}")

            # Fetch group data (will use cache if available)
            satellites = satellite_fetcher.fetch_group(group)

            if not satellites:
                print(f"  [WARN] No satellites found in group '{group}'")
                continue

            print(f"  Found {len(satellites)} satellites in cache")

            for sat in satellites:
                try:
                    norad_id = sat.get('NORAD_CAT_ID')
                    name = sat.get('OBJECT_NAME', 'Unknown')
                    tle_line1 = sat.get('TLE_LINE1')
                    tle_line2 = sat.get('TLE_LINE2')

                    if not all([norad_id, tle_line1, tle_line2]):
                        print(f"  [SKIP] {name}: Missing TLE data")
                        total_errors += 1
                        continue

                    # Check if satellite already exists
                    existing = get_satellite_by_norad_id(db, norad_id)

                    if existing:
                        # Update TLE if it exists
                        update_satellite_tle(db, existing.id, tle_line1, tle_line2)
                        total_updated += 1
                        if total_updated % 50 == 0:
                            print(f"  Updated {total_updated} satellites...")
                    else:
                        # Create new satellite
                        create_satellite(
                            db=db,
                            norad_id=norad_id,
                            name=name,
                            tle_line1=tle_line1,
                            tle_line2=tle_line2,
                            satellite_group=group,
                            satellite_type=None,  # Could infer from orbital parameters
                        )
                        total_added += 1
                        if total_added % 50 == 0:
                            print(f"  Added {total_added} satellites...")

                except Exception as e:
                    print(f"  [ERROR] Error processing {sat.get('OBJECT_NAME', 'unknown')}: {e}")
                    total_errors += 1

            print(f"  [OK] Completed group '{group}'")

        print("\n" + "="*60)
        print("[SUCCESS] Sync completed!")
        print(f"   Added: {total_added} satellites")
        print(f"   Updated: {total_updated} satellites")
        print(f"   Errors: {total_errors} satellites")
        print(f"   Total in database: {total_added + total_updated}")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n[ERROR] Sync failed: {e}")
        return False

    finally:
        db.close()


if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync satellites from cache to PostgreSQL database"
    )
    parser.add_argument(
        '--groups',
        nargs='+',
        default=None,
        help='Satellite groups to sync (default: all)'
    )

    args = parser.parse_args()

    print("Satellite Database Sync Tool")
    print("="*60)

    if args.groups:
        print(f"Syncing groups: {', '.join(args.groups)}")
    else:
        print("Syncing all default groups: stations, starlink, weather, gps, active")

    success = sync_satellites_to_db(groups=args.groups)

    sys.exit(0 if success else 1)
