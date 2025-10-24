"""
Satellite database model
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Satellite(Base):
    """
    Satellite model - stores satellite TLE data and metadata
    """
    __tablename__ = "satellites"

    id = Column(Integer, primary_key=True, index=True)
    norad_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)

    # TLE data
    tle_line1 = Column(Text, nullable=False)
    tle_line2 = Column(Text, nullable=False)
    tle_epoch = Column(DateTime, nullable=True)

    # Satellite classification
    satellite_group = Column(String(100), index=True, nullable=True)  # starlink, stations, weather, etc.
    satellite_type = Column(String(100), nullable=True)  # LEO, MEO, GEO, HEO

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Satellite(norad_id={self.norad_id}, name='{self.name}')>"
