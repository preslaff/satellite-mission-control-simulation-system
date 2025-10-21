"""
Satellite Mission Control & Simulation System - Main Application
FastAPI backend entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import API routes
from app.api.routes import satellites

# Import core configuration
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup: Initialize database, load ML models, start background tasks
    print("Starting Satellite Mission Control System...")

    yield

    # Shutdown: Cleanup resources
    print("Shutting down Satellite Mission Control System...")


# Create FastAPI application
app = FastAPI(
    title="Satellite Mission Control & Simulation API",
    description="High-fidelity orbital simulation and ML-powered trajectory prediction",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
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
        "message": "Satellite Mission Control API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "database": "pending",
            "ml_models": "pending",
        }
    }


# Include API routers
app.include_router(satellites.router, prefix="/api/satellites", tags=["Satellites"])
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
