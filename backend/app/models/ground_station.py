"""
Ground Station database model
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class GroundStation(Base):
    """
    Ground Station model - stores ground station locations and metadata
    """
    __tablename__ = "ground_stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=True)  # Station code (e.g., "NYC", "LON")

    # Location
    latitude = Column(Float, nullable=False)  # degrees
    longitude = Column(Float, nullable=False)  # degrees
    altitude = Column(Float, default=0.0)  # meters above sea level

    # Station capabilities
    min_elevation = Column(Float, default=10.0)  # minimum elevation angle in degrees
    max_range_km = Column(Float, nullable=True)  # maximum communication range in km

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<GroundStation(name='{self.name}', lat={self.latitude}, lon={self.longitude})>"
