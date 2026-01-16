import os
import sys
from app.database import engine, Base, SessionLocal
from app import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def create_admin_user():
    """Create default admin user"""
    db = SessionLocal()
    try:
        # Check if admin exists
        from app.auth import get_password_hash
        from app.models import User

        admin = db.query(User).filter(User.username == "admin").first()

        if not admin:
            admin = User(
                username="admin",
                email="admin@pos.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                full_name="Administrator",
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info("Admin user created: username=admin, password=admin123")
        else:
            logger.info("Admin user already exists")
        return True
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    tables_created = create_tables()
    if tables_created:
        create_admin_user()
    else:
        sys.exit(1)