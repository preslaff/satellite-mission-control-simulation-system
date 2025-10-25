# Satellite Mission Control Simulation System

![Satellite Mission Control Simulation System](preview.jpeg)

A comprehensive satellite mission control application with ML-powered trajectory prediction and course correction capabilities. Features real-time satellite tracking using SGP4 propagation, multiple coordinate system support, and high-fidelity orbital simulations.

**Current Status:** 65% complete - Backend operational, ML models in training, frontend functional with 3D visualization.

## ✨ Features

### Implemented ✓
- **Real-time satellite tracking** using SGP4 propagation
- **8,697 satellites tracked** (8,572 Starlink + 125 stations/weather/GPS)
- **Multiple coordinate systems** (ECI/GCRS, ECEF/ITRS, Geodetic, ENU, NED)
- **3D visualization** of Earth, orbits, and ground stations using Three.js
- **Ground station management** with visibility cone visualization
- **Satellite pass prediction** (rise/set times, azimuth/elevation)
- **PostgreSQL database** with persistent storage
- **WebSocket real-time updates** for telemetry streaming
- **TLE caching system** (2-hour cache, offline operation support)
- **Coordinate transformation service** using Skyfield (high-precision)

### In Development 🚧
- **ML trajectory prediction** (LSTM model trained, integration pending)
- **Anomaly detection** (VAE model trained, deployment pending)
- **Course correction optimizer** (RL framework designed, training pending)
- **Automated testing suite**
- **Docker deployment configuration**

## 🚀 Tech Stack

### Backend
- **Python 3.11** with FastAPI
- **PostgreSQL** for persistent storage
- **PyTorch** for ML models (LSTM, VAE, PPO)
- **Skyfield** for high-precision coordinate transformations
- **SGP4** for orbital propagation
- **WebSockets** for real-time communication

### Frontend
- **SvelteKit** for the web application
- **Threlte** (Three.js + Svelte) for 3D visualization
- **Svelte Stores** for reactive state management

### Data Science
- **Jupyter Notebooks** for research and prototyping
- **NumPy, Pandas** for data processing
- **Matplotlib, Seaborn** for visualization
- **scikit-learn** for preprocessing

## 📁 Project Structure

```
space-navigator/
├── backend/                        # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/            # API endpoints
│   │   │       ├── satellites.py  # Satellite tracking & orbital data
│   │   │       ├── ground_stations.py  # Ground station CRUD
│   │   │       ├── telemetry.py   # Telemetry endpoints
│   │   │       ├── coordinates.py # Coordinate transformations
│   │   │       └── websocket.py   # Real-time streaming
│   │   ├── core/
│   │   │   ├── config.py          # Configuration management
│   │   │   └── database.py        # Database connection
│   │   ├── models/
│   │   │   ├── satellite.py       # Satellite SQLAlchemy model
│   │   │   ├── ground_station.py  # Ground station model
│   │   │   └── telemetry.py       # Telemetry time-series model
│   │   ├── services/
│   │   │   ├── satellite_fetcher.py    # CelesTrak API client
│   │   │   └── coordinate_service.py   # Skyfield transformations
│   │   └── main.py                # FastAPI application entry
│   ├── notebooks/                 # Jupyter research notebooks
│   │   ├── 01_data_exploration.ipynb       # TLE data analysis
│   │   ├── 02_coordinate_systems.ipynb     # Coordinate validation
│   │   ├── 03_orbital_mechanics.ipynb      # SGP4 propagation study
│   │   └── 04_model_training.ipynb         # ML model training
│   ├── data/
│   │   ├── cache/                 # TLE cache (starlink, stations, etc.)
│   │   └── processed/             # Processed datasets for ML
│   ├── models/                    # Trained ML models
│   │   ├── trajectory_lstm.pth    # LSTM trajectory predictor
│   │   └── anomaly_vae.pth        # VAE anomaly detector
│   ├── requirements.txt
│   └── alembic/                   # Database migrations
├── frontend/                      # SvelteKit frontend
│   ├── src/
│   │   ├── routes/
│   │   │   └── +page.svelte       # Main application page
│   │   └── lib/
│   │       ├── components/
│   │       │   └── Globe3D.svelte # 3D Earth visualization
│   │       └── stores/
│   │           └── satellites.js  # Satellite state management
│   ├── package.json
│   └── vite.config.js
├── CLAUDE.md                      # Development plan & guidelines
├── DEVELOPMENT_STATUS.md          # Project completion status
├── FIXES_APPLIED.md               # Bug fix log
├── docker-compose.yml             # Docker orchestration (pending)
└── README.md                      # This file
```

## 🎯 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **PostgreSQL 14+** (with psycopg2 adapter)
- **Git**
- Docker & Docker Compose (optional, for containerized deployment)

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd space-navigator
```

#### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Database Setup

```bash
# Install PostgreSQL if not already installed
# Windows: Download installer from postgresql.org
# Linux: sudo apt-get install postgresql
# Mac: brew install postgresql

# Create database
createdb satcom

# Create user (if needed)
psql -c "CREATE USER satcom WITH PASSWORD 'satcom';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE satcom TO satcom;"
```

**Configure Database URL:**
Create `backend/.env` file:
```env
DATABASE_URL=postgresql://satcom:satcom@localhost:5432/satcom
```

#### 4. Run Database Migrations

```bash
cd backend

# Run Alembic migrations to create tables
alembic upgrade head
```

#### 5. Start Backend Server

```bash
cd backend

# Make sure virtual environment is activated
python -m uvicorn app.main:app --reload
```

Backend will be available at: http://localhost:8000

#### 6. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

### 🔬 Running Jupyter Notebooks

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Start Jupyter
jupyter lab

# Or use Jupyter Notebook
jupyter notebook
```

Open the notebooks in this order:
1. **01_data_exploration.ipynb** - Explore satellite TLE data and orbital parameters
2. **02_coordinate_systems.ipynb** - Validate coordinate transformations
3. **03_orbital_mechanics.ipynb** - SGP4 propagation and trajectory generation
4. **04_model_training.ipynb** - Train ML models (LSTM, VAE, RL)

## 📡 Usage

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Main application UI |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **Health Check** | http://localhost:8000/health | Service status |

### API Endpoints

#### Satellites
- `GET /api/satellites?group=starlink&limit=50` - List satellites by group
- `GET /api/satellites/{norad_id}` - Get specific satellite
- `GET /api/satellites/{norad_id}/orbit?duration=24&step=5` - Get orbital path
- `GET /api/satellites/{norad_id}/passes?lat=43.47&lon=27.78` - Predict passes
- `GET /api/satellites/{norad_id}/azel?lat=43.47&lon=27.78` - Current Az/El angles
- `GET /api/satellites/groups/available` - List satellite groups

#### Ground Stations
- `GET /api/ground-stations` - List all ground stations
- `POST /api/ground-stations` - Create ground station
- `GET /api/ground-stations/{id}` - Get specific station
- `PUT /api/ground-stations/{id}` - Update station
- `DELETE /api/ground-stations/{id}` - Delete station

#### Coordinates
- `GET /api/coordinates/satellite/{norad_id}?frame=ECI` - Get position in coordinate frame
  - Frames: `ECI`, `ECEF`, `GEODETIC`, `ENU`, `NED`
- `POST /api/coordinates/transform` - Transform between coordinate systems

#### Telemetry
- `GET /api/telemetry/{norad_id}/current` - Current satellite state
- `GET /api/telemetry/{norad_id}/history?hours=24` - Historical telemetry

#### WebSocket
- `WS /ws/telemetry` - Real-time telemetry stream

### Frontend Features

**3D Globe Visualization:**
- Real-time satellite positions
- Orbital trajectories (24-hour prediction)
- Ground station visibility cones
- Satellite pass trajectories
- Interactive camera controls

**Ground Station Management:**
- Add/remove ground stations
- Set latitude/longitude coordinates
- Configure minimum elevation angle
- Toggle visibility cone display
- Auto-calculate satellite passes

**Satellite Tracking:**
- Select from multiple satellite groups (Starlink, ISS, Weather, GPS)
- View current position and velocity
- See upcoming passes with rise/set times
- Track azimuth and elevation angles

### 🔍 Viewing More Satellites

**Important:** The 3D visualization displays a **limited number of satellites** (default: 50) for performance reasons. While the backend caches and tracks all 8,697 satellites, rendering all simultaneously would severely impact frame rate.

**To view more satellites:**

1. **Via API Query Parameters:**
   ```bash
   # Increase limit in API calls
   GET /api/satellites?group=starlink&limit=200

   # View all satellites (not recommended for 3D rendering)
   GET /api/satellites?group=starlink&limit=10000
   ```

2. **Frontend Code Modification:**
   Edit `frontend/src/routes/+page.svelte` and increase the `limit` parameter:
   ```javascript
   // Find the satellite fetch call and change limit:
   const response = await fetch(`${apiUrl}/api/satellites?group=starlink&limit=200`);
   ```

3. **Filtering by Group:**
   Instead of loading all Starlink satellites, switch between groups:
   ```bash
   # Space stations only (23 satellites)
   GET /api/satellites?group=stations

   # Weather satellites (70 satellites)
   GET /api/satellites?group=weather

   # GPS satellites (32 satellites)
   GET /api/satellites?group=gps
   ```

**Performance Recommendations:**
- **<100 satellites:** Smooth 60 FPS on most hardware
- **100-500 satellites:** 30-60 FPS (acceptable performance)
- **500-1000 satellites:** 15-30 FPS (noticeable lag)
- **>1000 satellites:** <15 FPS (poor user experience)

**Alternative for Full Catalog:**
- Use the API endpoints directly to query all satellites without 3D rendering
- Filter by orbital parameters, position, or visibility from ground stations
- Export data programmatically for analysis in Jupyter notebooks

## 📊 Data Sources

### Primary Sources
- **CelesTrak:** TLE data for 8,697 satellites (updated every 2 hours)
  - 8,572 Starlink satellites
  - 23 Space stations (ISS, CSS, etc.)
  - 70 Weather satellites
  - 32 GPS satellites

### Data Flow
1. **Fetch:** Backend fetches TLE data from CelesTrak on startup
2. **Cache:** Data cached in `backend/data/cache/*.json` (2-hour TTL)
3. **Propagate:** SGP4 calculates real-time positions
4. **Stream:** WebSocket pushes updates to frontend
5. **Database:** Optional persistent storage in PostgreSQL

### CelesTrak API Best Practices

**To avoid getting your IP blocked:**

- Cache duration: 2 hours (matches CelesTrak update frequency)
- Max retries: 3 attempts with 2-second delay
- Fallback to cache if API unavailable
- Persistent cache across restarts
- Avoid >10,000 HTTP 403 errors per day (auto-block)
- Use `celestrak.org` (not `.com`) to avoid redirects

**If blocked:** Stop requests, wait 2 hours, use cached data until unblocked.

## 🤖 Machine Learning Models

### 1. Trajectory Prediction (LSTM)
**Status:** Trained, integration pending

- **Architecture:** 2-layer LSTM with 128 hidden units
- **Input:** 12 time steps (1 hour history) of position/velocity
- **Output:** 12 time steps (1 hour prediction)
- **Features:** `[x, y, z, vx, vy, vz]` in ECI frame
- **Target:** <1 km position error at 24-hour horizon
- **Location:** `backend/models/trajectory_lstm.pth`

### 2. Anomaly Detection (VAE)
**Status:** Trained, integration pending

- **Architecture:** Variational Autoencoder with 8D latent space
- **Input:** 11 telemetry features (position, velocity, orbital elements)
- **Output:** Anomaly score (reconstruction error)
- **Threshold:** 95th percentile for anomaly flagging
- **Use case:** Detect deviations from normal orbital behavior
- **Location:** `backend/models/anomaly_vae.pth`

### 3. Course Correction Optimizer (RL - PPO)
**Status:** Framework designed, training pending

- **Algorithm:** Proximal Policy Optimization
- **State space:** Current/target orbital elements + fuel
- **Action space:** 3-axis delta-V burns (continuous)
- **Reward:** `-fuel_cost - time_penalty + accuracy_bonus`
- **Goal:** Optimize fuel-efficient orbital maneuvers
- **Note:** Requires GPU cluster for full training (24-48 hours)

## 🧪 Development Status

See `DEVELOPMENT_STATUS.md` for detailed breakdown.

**Overall Completion: 65%**

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Foundation & Data | Complete | 100% |
| Phase 2: Orbital Mechanics | Complete | 100% |
| Phase 3: ML Models | In Progress | 70% |
| Phase 4: Backend API | Complete | 100% |
| Phase 5: Frontend | Mostly Complete | 95% |
| Phase 6: ML Optimization | Pending | 0% |
| Phase 7: Testing & Deployment | In Progress | 40% |

### What's Working
- Backend API (12+ endpoints)
- Database persistence (PostgreSQL)
- Coordinate transformations (5 systems)
- SGP4 orbital propagation
- 3D visualization (Three.js)
- Ground station management
- Satellite pass prediction
- TLE caching system

### What's Pending
- ML model API integration
- Automated testing suite
- Docker deployment files
- RL training environment
- Production optimization

## 🛠️ Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://satcom:satcom@localhost:5432/satcom

# Optional: Space-Track.org (for additional TLE sources)
SPACETRACK_USERNAME=your_username
SPACETRACK_PASSWORD=your_password

# ML Models
MODEL_PATH=./models
```

### Frontend Configuration

Edit `frontend/vite.config.js` for:
- API proxy settings
- Development server port
- Build options

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
# or check Windows Services

# Test connection
psql -U satcom -d satcom -c "SELECT 1;"
```

**2. Frontend Can't Connect to Backend**
- Verify backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Ensure firewall allows localhost connections

**3. Satellites Not Loading**
- Check `backend/data/cache/` has TLE files
- Verify internet connection for CelesTrak
- Check backend logs for API errors

**4. Console Spam / Performance Issues**
- Fixed in `FIXES_APPLIED.md`
- Ensure you're on latest commit
- Check Globe3D.svelte has memoization fixes

## 📈 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | <100ms | ~50ms |
| Trajectory Prediction | <100ms | Training |
| Anomaly Detection | <50ms | Training |
| Frontend FPS | >30 FPS | 60 FPS |
| Database Queries | <10ms | ~5ms |
| WebSocket Latency | <50ms | ~20ms |

## 🧪 Testing

```bash
# Backend tests (pending)
cd backend
pytest

# Frontend tests (pending)
cd frontend
npm run test

# Manual API testing
# Open http://localhost:8000/docs
# Use Swagger UI for interactive testing
```

## 🚀 Deployment

### Production Checklist
- [ ] Create `Dockerfile` for backend
- [ ] Create `Dockerfile` for frontend
- [ ] Configure `docker-compose.yml`
- [ ] Set up Nginx reverse proxy
- [ ] Configure SSL certificates
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Load test with high satellite counts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow development guidelines in `CLAUDE.md`
4. Submit a pull request

## 📄 License

This project is for educational and research purposes.

## 🙏 Acknowledgments

- **NASA JPL** for orbital mechanics algorithms
- **CelesTrak** for TLE data and best practices
- **Skyfield** library for astronomical calculations
- **SGP4** library for satellite propagation
- **Three.js** for 3D visualization
- **FastAPI** for high-performance backend
- **SvelteKit** for reactive frontend

## 📚 Resources

- [CLAUDE.md](CLAUDE.md) - Detailed development plan
- [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) - Project completion tracking
- [FIXES_APPLIED.md](FIXES_APPLIED.md) - Bug fix history
- [CelesTrak API Docs](https://celestrak.org/NORAD/documentation/)
- [Skyfield Documentation](https://rhodesmill.org/skyfield/)
- [SGP4 Documentation](https://pypi.org/project/sgp4/)

---

**Last Updated:** 2025-10-25
**Version:** 0.1.0
**Status:** Active Development
