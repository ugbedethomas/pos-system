# app/database.py - CLEAN VERSION
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Render provides PostgreSQL, convert postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print("✅ Using PostgreSQL database")
    engine = create_engine(database_url)
else:
    # Local development with SQLite
    print("✅ Using SQLite database: pos.db")
    engine = create_engine(
        "sqlite:///./pos.db",
        connect_args={"check_same_thread": False}
    )

# Create session and base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()