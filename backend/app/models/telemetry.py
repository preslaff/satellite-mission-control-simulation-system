"""
Telemetry database model for time-series satellite state data
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Telemetry(Base):
    """
    Telemetry model - stores time-series satellite position and velocity data
    Optimized for TimescaleDB hypertable (if used)
    """
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"), primary_key=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)

    # Position in ECI (J2000) coordinates (km)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)

    # Velocity in ECI (J2000) coordinates (km/s)
    velocity_x = Column(Float, nullable=False)
    velocity_y = Column(Float, nullable=False)
    velocity_z = Column(Float, nullable=False)

    # Optional: Altitude and velocity magnitude for quick queries
    altitude_km = Column(Float, nullable=True)
    velocity_km_s = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: Composite primary key (id, satellite_id, timestamp) eliminates need for separate index
    # TimescaleDB requires timestamp to be part of primary key for hypertable partitioning

    def __repr__(self):
        return f"<Telemetry(satellite_id={self.satellite_id}, timestamp='{self.timestamp}')>"
