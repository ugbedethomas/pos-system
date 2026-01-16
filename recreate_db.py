print("🔄 Recreating database tables...")

try:
    from app.database import engine, Base
    from app import models

    # Drop all tables and recreate them
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database tables recreated successfully!")
    print("✅ Tables created: products, customers, sales, sale_items, stock_movements")
    print("✅ New column: products.min_stock_level")

except Exception as e:
    print(f"❌ ERROR: {e}")