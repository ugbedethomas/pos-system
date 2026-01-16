print("🧪 Simple SQLAlchemy 1.3 Test")
print("=" * 40)

try:
    # Basic import test
    import sqlalchemy

    print(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")

    # Try to create engine
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///./test.db")
    print("✅ Engine created successfully")

    # Try basic query
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()
    print("✅ Session created successfully")

    session.close()
    print("\n🎉 SQLAlchemy 1.3 works with Python 3.13!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback

    traceback.print_exc()