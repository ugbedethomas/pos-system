Write-Host " GUARANTEED FIX FOR RENDER DEPLOYMENT" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Create standalone init script
Write-Host "`n1. Creating standalone initialization script..." -ForegroundColor Yellow
@'
#!/usr/bin/env python3
# init_render.py - Standalone initialization
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.database import Base, engine, SessionLocal
    from app import models
    from app.auth import get_password_hash
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    from app.models import User
    
    # Create users
    users = [
        ("admin", "admin123", "admin", "Administrator"),
        ("cashier", "cashier123", "cashier", "Cashier"),
        ("inventory", "inventory123", "inventory", "Inventory Manager")
    ]
    
    for username, password, role, full_name in users:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            new_user = User(
                username=username,
                email=f"{username}@pos.com",
                hashed_password=get_password_hash(password),
                role=role,
                full_name=full_name,
                is_active=True
            )
            db.add(new_user)
            print(f"Created user: {username}/{password}")
    
    db.commit()
    db.close()
    print(" SUCCESS! Database initialized.")
    
except Exception as e:
    print(f" ERROR: {e}")
    sys.exit(1)
