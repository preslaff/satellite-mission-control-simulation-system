"""
Database connection and session management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,  # Maximum number of connections to keep
    max_overflow=20,  # Maximum overflow connections
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session

    Usage in FastAPI routes:
    @app.get("/endpoint")
    def endpoint(db: Session = Depends(get_db)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables
    This should be called on application startup
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def check_db_connection() -> bool:
    """
    Check if database connection is healthy
    Returns True if connection is successful, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
