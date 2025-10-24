"""
Satellite Mission Control Simulation System - Main Application
FastAPI backend entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import API routes
from app.api.routes import satellites, websocket

# Import core configuration
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup: Initialize database, load ML models, start background tasks
    print("Starting Satellite Mission Control Simulation System...")

    # Import database functions
    from app.core.database import init_db, check_db_connection

    # Check database connection
    if check_db_connection():
        print("Database connection successful")
        # Initialize database tables (create if they don't exist)
        # init_db()  # Uncomment this to auto-create tables on startup
    else:
        print("WARNING: Database connection failed - some features may not work")
        print("Please ensure PostgreSQL is running and configured correctly")

    yield

    # Shutdown: Cleanup resources
    print("Shutting down Satellite Mission Control Simulation System...")


# Create FastAPI application
app = FastAPI(
    title="Satellite Mission Control Simulation System API",
    description="High-fidelity orbital simulation and ML-powered trajectory prediction",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for WebSocket and API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Standard Vite dev server port
        "http://localhost:5174",  # Alternative Vite dev server port
        "http://127.0.0.1:5173",  # Localhost variant
        "http://127.0.0.1:5174",  # Localhost variant
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "status": "operational",
        "message": "Satellite Mission Control Simulation System API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    from app.core.database import check_db_connection

    db_status = "operational" if check_db_connection() else "unavailable"

    return {
        "status": "healthy" if db_status == "operational" else "degraded",
        "services": {
            "api": "operational",
            "database": db_status,
            "ml_models": "pending",
        }
    }


# Include API routers
app.include_router(satellites.router, prefix="/api/satellites", tags=["Satellites"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
# app.include_router(coordinates.router, prefix="/api/coordinates", tags=["Coordinates"])
# app.include_router(telemetry.router, prefix="/api/telemetry", tags=["Telemetry"])
# app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
