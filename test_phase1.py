print("🧪 PHASE 1 TEST: Database Setup")
print("=" * 40)

try:
    # Test 1: Import modules
    from app.database import engine, SessionLocal, Base
    from app.models import Product

    print("✅ Test 1: All imports successful")

    # Test 2: Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Test 2: Database tables created")

    # Test 3: Connect to database
    db = SessionLocal()
    product_count = db.query(Product).count()
    print("✅ Test 3: Database connection successful")
    print(f"   Current products in DB: {product_count}")

    # Test 4: Add a test product
    if product_count == 0:
        test_product = Product(
            name="Sample Coffee",
            price=4.99,
            stock_quantity=50,
            sku="COFF-001",
            category="Beverages"
        )
        db.add(test_product)
        db.commit()
        print("✅ Test 4: Added test product to database")

    # Test 5: Query the product
    products = db.query(Product).all()
    for p in products:
        print(f"   📦 Product: {p.name} - ${p.price} - Stock: {p.stock_quantity}")

    db.close()

    print("\n" + "=" * 40)
    print("🎉 PHASE 1 COMPLETE! Database is working!")
    print("\n✅ All tests passed!")
    print("✅ You should see a 'pos.db' file in your project")
    print("✅ Ready for Phase 2: Product Management API")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("❌ Check your code and try again")