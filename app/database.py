import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment variable (Render provides this)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Render provides PostgreSQL, convert postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    logger.info(f"Using PostgreSQL database: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
else:
    # Local development with SQLite
    SQLALCHEMY_DATABASE_URL = "sqlite:///./pos.db"
    logger.info(f"Using SQLite database: {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()