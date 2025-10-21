"""
Configuration management for the Satellite Mission Control System
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    # Application
    APP_NAME: str = "Satellite Mission Control & Simulation System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "postgresql://satcom:satcom@localhost:5432/satcom"

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # ML Models
    MODEL_PATH: str = "data/models"
    TRAJECTORY_MODEL_NAME: str = "trajectory_predictor.pth"
    ANOMALY_MODEL_NAME: str = "anomaly_detector.pth"
    COURSE_CORRECTION_MODEL_NAME: str = "course_correction.pth"

    # Orbital Mechanics
    SGP4_PROPAGATOR: str = "sgp4"
    COORDINATE_PRECISION: str = "high"  # high, medium, low

    # Data Sources
    CELESTRAK_URL: str = "https://celestrak.org/NORAD/elements/"
    SPACETRACK_URL: str = "https://www.space-track.org"
    SPACETRACK_USERNAME: Optional[str] = None
    SPACETRACK_PASSWORD: Optional[str] = None

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MESSAGE_QUEUE_SIZE: int = 100

    # Simulation
    DEFAULT_TIME_STEP: float = 1.0  # seconds
    MAX_PROPAGATION_DAYS: int = 365

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
