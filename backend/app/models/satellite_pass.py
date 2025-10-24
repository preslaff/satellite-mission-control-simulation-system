"""
Satellite Pass database model
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class SatellitePass(Base):
    """
    Satellite Pass model - stores predicted satellite passes over ground stations
    """
    __tablename__ = "satellite_passes"

    id = Column(Integer, primary_key=True, index=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"), nullable=False, index=True)
    ground_station_id = Column(Integer, ForeignKey("ground_stations.id"), nullable=False, index=True)

    # Pass timing
    rise_time = Column(DateTime(timezone=True), nullable=False)
    set_time = Column(DateTime(timezone=True), nullable=False)
    max_elevation_time = Column(DateTime(timezone=True), nullable=False)

    # Pass characteristics
    max_elevation = Column(Float, nullable=False)  # degrees
    rise_azimuth = Column(Float, nullable=False)  # degrees
    set_azimuth = Column(Float, nullable=False)  # degrees
    duration_seconds = Column(Float, nullable=False)  # seconds

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_passes_sat_station', 'satellite_id', 'ground_station_id'),
        Index('idx_passes_rise_time', 'rise_time'),
    )

    def __repr__(self):
        return f"<SatellitePass(sat_id={self.satellite_id}, station_id={self.ground_station_id}, rise='{self.rise_time}')>"
