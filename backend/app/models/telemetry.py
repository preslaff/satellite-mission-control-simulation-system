"""
Telemetry database model for time-series satellite state data
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class Telemetry(Base):
    """
    Telemetry model - stores time-series satellite position and velocity data
    Optimized for TimescaleDB hypertable (if used)

    Note: Uses single ID primary key instead of composite for TimescaleDB compatibility.
    Unique constraint on (satellite_id, timestamp) ensures no duplicates.
    """
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

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

    # Unique constraint to prevent duplicate telemetry for same satellite at same time
    __table_args__ = (
        UniqueConstraint('satellite_id', 'timestamp', name='uq_satellite_timestamp'),
    )

    def __repr__(self):
        return f"<Telemetry(id={self.id}, satellite_id={self.satellite_id}, timestamp='{self.timestamp}')>"
