# Satellite Tracking Datasets for ML Training

## Quick Start - Best Datasets

### 1. **CelesTrak (Recommended - Free, No Registration)**
**Best for**: Real-time TLE data, Starlink satellites, comprehensive coverage

**URL**: https://celestrak.org/NORAD/elements/

**What you get**:
- Two-Line Element (TLE) sets for all tracked satellites
- Updated multiple times daily
- 25,000+ active satellites
- Historical archives available

**API Access** (New Format):
```python
# Get Starlink satellites
https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json

# Get last 30 days of launches
https://celestrak.org/NORAD/elements/gp.php?GROUP=last-30-days&FORMAT=csv

# Get specific satellite by catalog number
https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle  # ISS

# Available formats: TLE, JSON, CSV, XML, KVN
```

**Popular Groups**:
- `starlink` - ~6,500 Starlink satellites
- `stations` - ISS and space stations
- `weather` - Weather satellites
- `active` - All active satellites
- `gps-ops` - GPS constellation
- `iridium-NEXT` - Iridium satellites

**Python Example**:
```python
import requests
import json

# Fetch Starlink data in JSON format
url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json"
response = requests.get(url)
satellites = response.json()

# Each satellite has:
# - OBJECT_NAME, NORAD_CAT_ID
# - EPOCH, MEAN_MOTION
# - ECCENTRICITY, INCLINATION
# - RA_OF_ASC_NODE, ARG_OF_PERICENTER, MEAN_ANOMALY
# - And more orbital elements

print(f"Retrieved {len(satellites)} satellites")
print(satellites[0])  # First satellite data
```

---

### 2. **Space-Track.org (Requires Free Registration)**
**Best for**: Historical TLE data, comprehensive archives, official US Space Force data

**URL**: https://www.space-track.org

**What you get**:
- 138+ million historical TLE records
- Official USSPACECOM orbital data
- Advanced filtering and queries
- Conjunction data messages (CDMs)
- Satellite catalog (SATCAT) metadata

**Registration**: Free but requires:
- Name, email, country
- Purpose of use (research/education acceptable)
- User agreement acceptance

**API Access**:
```python
import requests

# Login credentials
username = "your_email@example.com"
password = "your_password"

# Create session
session = requests.Session()
login_url = "https://www.space-track.org/ajaxauth/login"
session.post(login_url, data={'identity': username, 'password': password})

# Query Starlink satellites
query = "https://www.space-track.org/basicspacedata/query/class/gp/NORAD_CAT_ID/>40000/OBJECT_NAME/STARLINK~~/orderby/NORAD_CAT_ID/format/json"
response = session.get(query)
data = response.json()

# Get historical TLE for specific satellite
# GP_History class provides historical records
hist_query = "https://www.space-track.org/basicspacedata/query/class/gp_history/NORAD_CAT_ID/25544/orderby/EPOCH asc/format/json"
historical = session.get(hist_query)
```

**Pro Tip**: Space-Track has rate limits (30 requests/minute). Cache data locally!

---

### 3. **Kaggle Datasets**

#### **a) Satellite Trajectory Prediction Dataset**
**URL**: https://www.kaggle.com/datasets/idawoodjee/predict-the-positions-and-speeds-of-600-satellites

**What you get**:
- 600 satellites
- 7-day trajectories
- Position (x, y, z) and velocity (vx, vy, vz)
- Pre-processed for ML training
- **Perfect for your TODO!**

**Features**:
- Time series data
- Multiple satellites
- Ready for LSTM/Transformer training

#### **b) Starlink TLE Dataset (April 2025)**
**URL**: https://www.kaggle.com/datasets/vijayj0shi/starlink-satellite-tlecsv-dataset-april-2025

**What you get**:
- CSV format
- Starlink-specific data
- Recent snapshot (April 2025)
- Easy to import and analyze

#### **c) Active Satellites Database**
**URL**: https://www.kaggle.com/datasets/ucsusa/active-satellites

**What you get**:
- Satellite metadata
- Country of origin
- Purpose (communications, Earth observation, etc.)
- Launch dates
- Orbital characteristics

---

## Data Processing Pipeline

### Step 1: Fetch TLE Data
```python
from sgp4.api import Satellite, jday
import numpy as np
from datetime import datetime, timedelta

def fetch_starlink_tles():
    """Fetch current Starlink TLEs from CelesTrak"""
    import requests
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json"
    response = requests.get(url)
    return response.json()

# Fetch data
satellites_data = fetch_starlink_tles()
print(f"Fetched {len(satellites_data)} satellites")
```

### Step 2: Convert TLE to Position/Velocity
```python
def tle_to_state_vectors(tle_data, time_points):
    """
    Convert TLE to position and velocity vectors over time
    
    Args:
        tle_data: dict with orbital elements from CelesTrak
        time_points: list of datetime objects
    
    Returns:
        positions: array of [x, y, z] in km
        velocities: array of [vx, vy, vz] in km/s
    """
    from sgp4.api import Satellite
    from sgp4.api import jday
    
    # Create SGP4 satellite object
    sat = Satellite(
        satnum=tle_data['NORAD_CAT_ID'],
        epoch=tle_data['EPOCH'],
        bstar=tle_data.get('BSTAR', 0),
        ndot=tle_data.get('MEAN_MOTION_DOT', 0),
        nddot=tle_data.get('MEAN_MOTION_DDOT', 0),
        ecco=tle_data['ECCENTRICITY'],
        argpo=np.radians(tle_data['ARG_OF_PERICENTER']),
        inclo=np.radians(tle_data['INCLINATION']),
        mo=np.radians(tle_data['MEAN_ANOMALY']),
        no_kozai=tle_data['MEAN_MOTION'] * 2 * np.pi / 1440.0,  # rev/day to rad/min
        nodeo=np.radians(tle_data['RA_OF_ASC_NODE'])
    )
    
    positions = []
    velocities = []
    
    for t in time_points:
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
        e, r, v = sat.sgp4(jd, fr)
        
        if e == 0:  # No error
            positions.append(r)  # km
            velocities.append(v)  # km/s
        else:
            positions.append([np.nan, np.nan, np.nan])
            velocities.append([np.nan, np.nan, np.nan])
    
    return np.array(positions), np.array(velocities)
```

### Step 3: Generate Training Data
```python
def generate_training_dataset(num_satellites=100, days=30):
    """
    Generate ML training dataset
    
    Returns:
        features: [samples, timesteps, 6] - position + velocity
        targets: [samples, prediction_horizons, 6] - future states
    """
    # Fetch TLEs
    all_sats = fetch_starlink_tles()
    selected_sats = all_sats[:num_satellites]
    
    # Time configuration
    start_time = datetime.utcnow() - timedelta(days=days)
    
    features = []
    targets_1h = []
    targets_6h = []
    targets_24h = []
    
    for sat_data in selected_sats:
        # Historical window (24 hours of data points, every 5 minutes)
        hist_times = [start_time + timedelta(minutes=5*i) for i in range(288)]
        
        # Future prediction points
        future_1h = start_time + timedelta(hours=25)
        future_6h = start_time + timedelta(hours=30)
        future_24h = start_time + timedelta(hours=48)
        
        # Get state vectors
        pos_hist, vel_hist = tle_to_state_vectors(sat_data, hist_times)
        pos_1h, vel_1h = tle_to_state_vectors(sat_data, [future_1h])
        pos_6h, vel_6h = tle_to_state_vectors(sat_data, [future_6h])
        pos_24h, vel_24h = tle_to_state_vectors(sat_data, [future_24h])
        
        # Combine position and velocity
        state_hist = np.concatenate([pos_hist, vel_hist], axis=1)  # [288, 6]
        state_1h = np.concatenate([pos_1h[0], vel_1h[0]])  # [6]
        state_6h = np.concatenate([pos_6h[0], vel_6h[0]])  # [6]
        state_24h = np.concatenate([pos_24h[0], vel_24h[0]])  # [6]
        
        features.append(state_hist)
        targets_1h.append(state_1h)
        targets_6h.append(state_6h)
        targets_24h.append(state_24h)
    
    return {
        'features': np.array(features),
        'targets': {
            '1h': np.array(targets_1h),
            '6h': np.array(targets_6h),
            '24h': np.array(targets_24h)
        }
    }

# Generate dataset
dataset = generate_training_dataset(num_satellites=100, days=30)
print(f"Features shape: {dataset['features'].shape}")
print(f"Target 1h shape: {dataset['targets']['1h'].shape}")
```

---

## Complete Data Pipeline Script

```python
import requests
import numpy as np
from datetime import datetime, timedelta
from sgp4.api import Satellite, jday
import pandas as pd

class SatelliteDataFetcher:
    """Fetch and process satellite data for ML training"""
    
    def __init__(self, source='celestrak'):
        self.source = source
        self.base_url = "https://celestrak.org/NORAD/elements/"
    
    def fetch_group(self, group='starlink', format='json'):
        """Fetch satellite group from CelesTrak"""
        url = f"{self.base_url}gp.php?GROUP={group}&FORMAT={format}"
        response = requests.get(url)
        return response.json() if format == 'json' else response.text
    
    def fetch_by_norad_id(self, norad_id, format='json'):
        """Fetch specific satellite by NORAD catalog number"""
        url = f"{self.base_url}gp.php?CATNR={norad_id}&FORMAT={format}"
        response = requests.get(url)
        data = response.json()
        return data[0] if data else None
    
    def propagate_orbit(self, tle_data, duration_hours=24, step_minutes=5):
        """
        Propagate orbit forward in time
        
        Returns:
            DataFrame with columns: time, x, y, z, vx, vy, vz
        """
        # Parse epoch
        epoch_str = tle_data['EPOCH']
        epoch = datetime.strptime(epoch_str, '%Y-%m-%dT%H:%M:%S.%f')
        
        # Time points
        num_steps = int(duration_hours * 60 / step_minutes)
        times = [epoch + timedelta(minutes=step_minutes*i) for i in range(num_steps)]
        
        # Propagate
        positions, velocities = tle_to_state_vectors(tle_data, times)
        
        # Create DataFrame
        df = pd.DataFrame({
            'time': times,
            'x': positions[:, 0],
            'y': positions[:, 1],
            'z': positions[:, 2],
            'vx': velocities[:, 0],
            'vy': velocities[:, 1],
            'vz': velocities[:, 2],
            'sat_name': tle_data['OBJECT_NAME'],
            'norad_id': tle_data['NORAD_CAT_ID']
        })
        
        return df
    
    def create_ml_dataset(self, satellites, lookback_hours=24, 
                         predict_horizons=[1, 6, 24]):
        """
        Create ML dataset with features and targets
        
        Args:
            satellites: list of TLE data dicts
            lookback_hours: hours of historical data for features
            predict_horizons: list of hours to predict into future
        
        Returns:
            features, targets dictionary
        """
        all_features = []
        all_targets = {h: [] for h in predict_horizons}
        
        for sat in satellites:
            # Historical data (features)
            hist_df = self.propagate_orbit(sat, duration_hours=lookback_hours, 
                                          step_minutes=5)
            
            # Future data (targets)
            for horizon in predict_horizons:
                future_df = self.propagate_orbit(sat, duration_hours=horizon, 
                                                step_minutes=horizon*60)
                target_state = future_df.iloc[-1][['x', 'y', 'z', 'vx', 'vy', 'vz']].values
                all_targets[horizon].append(target_state)
            
            # Features: [timesteps, 6 features]
            feature_array = hist_df[['x', 'y', 'z', 'vx', 'vy', 'vz']].values
            all_features.append(feature_array)
        
        return {
            'features': np.array(all_features),
            'targets': {h: np.array(v) for h, v in all_targets.items()}
        }

# Usage Example
fetcher = SatelliteDataFetcher()

# Fetch Starlink satellites
starlink_sats = fetcher.fetch_group('starlink')
print(f"Fetched {len(starlink_sats)} Starlink satellites")

# Create dataset for first 100 satellites
dataset = fetcher.create_ml_dataset(starlink_sats[:100])

print(f"Features shape: {dataset['features'].shape}")
print(f"Targets shapes:")
for horizon, targets in dataset['targets'].items():
    print(f"  {horizon}h: {targets.shape}")

# Save to disk
np.savez_compressed('satellite_dataset.npz', 
                   features=dataset['features'],
                   **{f'target_{h}h': v for h, v in dataset['targets'].items()})
```

---

## Additional Data Sources

### 4. **Jonathan McDowell's Space Archive**
**URL**: https://planet4589.org/space/gcat

**What you get**:
- Historical satellite data going back to Sputnik (1957)
- Detailed launch records
- Satellite specifications
- Best for historical analysis

### 5. **N2YO.com API**
**URL**: https://www.n2yo.com/api/

**What you get**:
- Real-time satellite positions
- Visual passes predictions
- Radio passes
- Commercial API (free tier available)

### 6. **Satellite Catalog (SATCAT)**
**URL**: https://celestrak.com/pub/satcat.csv

**What you get**:
- 52,000+ objects (satellites + debris)
- Launch dates, decay dates
- Country of origin
- Orbital parameters
- CSV format, easy to analyze

---

## Recommended Dataset Strategy

For your ML project, I recommend this combination:

1. **Primary Training Data**: CelesTrak API
   - Free, no registration
   - Real-time updates
   - Easy API access
   - Focus on Starlink for large, homogeneous dataset

2. **Historical Validation**: Space-Track.org
   - Register once, use forever
   - Access to historical TLEs for validation
   - Test model on past data to verify accuracy

3. **Pre-built ML Dataset**: Kaggle 600 Satellites
   - Quick start for model development
   - Pre-processed data
   - Benchmark against published results

4. **Metadata**: SATCAT CSV
   - Satellite specifications
   - Filter by type, country, orbit
   - Enrich your training data

---

## Quick Start Code

Save this as `fetch_satellite_data.py`:

```python
#!/usr/bin/env python3
"""
Fetch satellite data and create ML training dataset
"""
import requests
import numpy as np
from datetime import datetime, timedelta
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', default='starlink', help='Satellite group')
    parser.add_argument('--num-sats', type=int, default=100)
    parser.add_argument('--output', default='satellite_data.npz')
    args = parser.parse_args()
    
    # Fetch TLEs
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={args.group}&FORMAT=json"
    print(f"Fetching {args.group} satellites...")
    response = requests.get(url)
    satellites = response.json()[:args.num_sats]
    print(f"Fetched {len(satellites)} satellites")
    
    # TODO: Process into training data
    # (Use SatelliteDataFetcher class from above)
    
    print(f"Saved to {args.output}")

if __name__ == '__main__':
    main()
```

Run with:
```bash
python fetch_satellite_data.py --group starlink --num-sats 100
```

---

## Data Quality Notes

- **TLE Accuracy**: TLEs are accurate for ~1-2 weeks after epoch
- **Update Frequency**: CelesTrak updates several times per day
- **Missing Data**: Some classified satellites have no TLEs
- **Coordinate Frame**: SGP4 outputs in TEME (True Equator Mean Equinox)
- **Propagation Limits**: Don't propagate TLEs >2 weeks from epoch

Good luck with your satellite tracking ML project! 🛰️
