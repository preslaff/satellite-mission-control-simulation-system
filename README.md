# Satellite Mission Control Simulation System

A comprehensive satellite mission control application with ML-powered trajectory prediction and course correction capabilities. Features real-time satellite tracking, multiple coordinate system support, and high-fidelity orbital simulations.

## Features

- Real-time satellite tracking using SGP4 propagation
- Multiple coordinate systems (ECI, ECEF, Topocentric)
- 3D visualization of Earth and satellite orbits
- ML-powered trajectory prediction
- Anomaly detection in telemetry data
- Course correction optimization using reinforcement learning
- WebSocket-based real-time updates
- Historical telemetry analysis

## Tech Stack

### Backend
- **Python 3.11** with FastAPI
- **PostgreSQL + TimescaleDB** for time-series data
- **PyTorch** for ML models
- **Skyfield & SGP4** for orbital mechanics
- **WebSockets** for real-time communication

### Frontend
- **SvelteKit** for the web application
- **Threlte** (Three.js + Svelte) for 3D visualization
- **Axios** for API communication
- **Svelte Stores** for state management

### Data Science
- **Jupyter Notebooks** for exploration and prototyping
- **NumPy, Pandas** for data processing
- **Matplotlib, Seaborn** for visualization

## Project Structure

```
space-navigator/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── core/              # Core functionality
│   │   │   ├── coordinates/   # Coordinate systems
│   │   │   └── orbital/       # Orbital mechanics
│   │   ├── models/            # Database models
│   │   ├── ml/                # ML models
│   │   ├── services/          # Business logic
│   │   └── main.py           # Application entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # SvelteKit frontend
│   ├── src/
│   │   ├── routes/            # SvelteKit routes
│   │   └── lib/
│   │       ├── components/    # Svelte components
│   │       ├── services/      # API & WebSocket clients
│   │       └── stores/        # Svelte stores
│   ├── package.json
│   └── Dockerfile
├── notebooks/                  # Jupyter notebooks
│   ├── 01_getting_started.ipynb
│   ├── 02_coordinate_systems.ipynb
│   ├── 03_orbital_mechanics.ipynb
│   ├── 04_model_training.ipynb
│   └── 05_data_exploration.ipynb
├── data/
│   ├── raw/                   # Raw TLE and satellite data
│   ├── processed/             # Cleaned data
│   └── models/                # Trained ML models
├── docker-compose.yml
└── CLAUDE.md                  # Development guidelines
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- PostgreSQL 14+ (if not using Docker)

### Installation

#### Option 1: Local Development

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run backend server
python -m uvicorn app.main:app --reload
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

**Database Setup (if not using Docker):**
```bash
# Install PostgreSQL with TimescaleDB extension
# Create database
createdb satcom

# Update DATABASE_URL in backend/.env
```

#### Option 2: Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Running Jupyter Notebooks

```bash
cd notebooks

# Activate backend virtual environment
source ../backend/venv/bin/activate

# Start Jupyter
jupyter notebook
```

## Usage

### Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### API Endpoints

#### Satellites
- `GET /api/satellites` - List all tracked satellites
- `GET /api/satellites/{id}` - Get satellite details
- `POST /api/satellites` - Add new satellite

#### Coordinates
- `POST /api/coordinates/transform` - Transform between coordinate systems
- `GET /api/coordinates/satellite/{id}` - Get satellite position in specified system

#### Telemetry
- `GET /api/telemetry/{id}/current` - Current satellite state
- `GET /api/telemetry/{id}/history` - Historical telemetry data

#### Predictions
- `POST /api/predictions/trajectory` - Predict future trajectory
- `POST /api/predictions/collision` - Collision risk assessment

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## Development Workflow

### Phase 1: Data Exploration
1. Run `01_getting_started.ipynb` for coordinate systems overview
2. Use `05_data_exploration.ipynb` to fetch TLE data
3. Explore `02_coordinate_systems.ipynb` for transformations

### Phase 2: Orbital Mechanics
1. Implement SGP4 propagation in `03_orbital_mechanics.ipynb`
2. Validate against real satellite data
3. Integrate into backend

### Phase 3: ML Models
1. Train models in `04_model_training.ipynb`
2. Export to `data/models/`
3. Integrate with backend API

### Phase 4: Frontend Development
1. Implement 3D visualization with Threlte
2. Connect to backend API
3. Add real-time WebSocket updates

## Configuration

### Backend Environment Variables

See `backend/.env.example` for all available options:

- `DATABASE_URL` - PostgreSQL connection string
- `SPACETRACK_USERNAME` - Space-Track.org credentials
- `SPACETRACK_PASSWORD` - Space-Track.org password
- `MODEL_PATH` - Path to ML models

### Frontend Configuration

Edit `frontend/vite.config.js` to configure:
- API proxy settings
- Development server port
- Build options

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

## Deployment

### Production Build

```bash
# Build frontend
cd frontend
npm run build

# Start production stack
docker-compose --profile production up -d
```

### Environment Setup

1. Update `.env` files with production credentials
2. Configure database backups
3. Set up SSL certificates (nginx)
4. Configure monitoring and logging

## Data Sources

- **CelesTrak:** https://celestrak.org/NORAD/elements/
- **Space-Track.org:** https://www.space-track.org (requires registration)
- **SpaceX API:** https://api.spacexdata.com/v4/

## ML Model Performance Targets

- **Trajectory Prediction:** Position error <1km at 24h horizon
- **Anomaly Detection:** Precision >90%, Recall >85%
- **Course Correction:** Fuel savings >10% vs baseline

## Contributing

See development guidelines in `CLAUDE.md` for detailed implementation plans.

## License

This project is for educational and research purposes.

## Acknowledgments

- NASA JPL for orbital mechanics algorithms
- CelesTrak for TLE data
- SpaceX for launch data
- Skyfield library for astronomical calculations
