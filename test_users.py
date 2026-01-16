print("🧪 Testing User Authentication Setup")

try:
    # Check imports
    from app.models import User

    print("✅ User model imported successfully")

    # Check database
    from app.database import SessionLocal, engine, Base
    from app import models

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Try to query users
    users = db.query(User).all()
    print(f"✅ Database connection successful")
    print(f"✅ Found {len(users)} users in database")

    # Try to create a user
    from app.auth import get_password_hash

    test_user = User(
        username="test",
        full_name="Test User",
        email="test@example.com",
        hashed_password=get_password_hash("test123"),
        role="admin"
    )

    db.add(test_user)
    db.commit()
    print("✅ Created test user successfully")

    # Try authentication
    from app.auth import authenticate_user, verify_password

    user = db.query(User).filter(User.username == "test").first()
    if user and verify_password("test123", user.hashed_password):
        print("✅ Password verification works")
    else:
        print("❌ Password verification failed")

    # Clean up
    db.query(User).filter(User.username == "test").delete()
    db.commit()

    db.close()
    print("\n🎉 User authentication system is ready!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback

    traceback.print_exc()