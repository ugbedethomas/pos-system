import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# FIX: Always use PostgreSQL on Render, SQLite locally
if DATABASE_URL:
    # Render PostgreSQL - fix URL format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print(f"✅ Using PostgreSQL database (Render)")
    engine = create_engine(DATABASE_URL)
else:
    # Local development - SQLite
    DATABASE_URL = "sqlite:///pos.db"
    print(f"✅ Using SQLite database: pos.db")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base
Base = declarative_base()