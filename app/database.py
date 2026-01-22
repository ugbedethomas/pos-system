import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment variable (Render provides this)
DATABASE_URL_ENV = os.environ.get('DATABASE_URL')  # Changed variable name


def get_database_url():
    """Get the database URL with proper configuration"""
    if DATABASE_URL_ENV:  # Use the new variable name
        # Render provides PostgreSQL, convert postgres:// to postgresql://
        if DATABASE_URL_ENV.startswith('postgres://'):
            DATABASE_URL_ENV = DATABASE_URL_ENV.replace('postgres://', 'postgresql://', 1)

        logger.info(f"Using PostgreSQL database (Persistent on Render)")
        return DATABASE_URL_ENV
    else:
        # Local development with SQLite
        IS_RENDER = os.environ.get('RENDER') or os.environ.get('DATABASE_URL')

        if IS_RENDER:
            # On Render free tier, use /tmp directory which persists
            SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/pos.db"
            logger.info("Using SQLite in /tmp directory (Persists on Render)")
        else:
            # Local development
            SQLALCHEMY_DATABASE_URL = "sqlite:///./pos.db"
            logger.info("Using local SQLite database")

        return SQLALCHEMY_DATABASE_URL


# Create engine with proper settings
database_url = get_database_url()

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    pool_pre_ping=True if "postgresql" in database_url else False,
    pool_recycle=300 if "postgresql" in database_url else None
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False