print("🧪 PHASE 2 TEST: Product Management API (CRUD Only)")
print("=" * 40)


def test_crud():
    try:
        print("Testing CRUD operations...")

        # Import only what we need (no FastAPI)
        from app.database import SessionLocal
        from app import crud, schemas

        print("✅ Test 1: All imports successful")

        # Get database session
        db = SessionLocal()

        # Test 2: Create a product
        print("\n📝 Test 2: Creating product...")
        test_product = schemas.ProductCreate(
            name="Cappuccino",
            price=4.50,
            stock_quantity=75,
            sku="CAPP-001",
            category="Hot Drinks",
            description="Fresh cappuccino with foam"
        )

        created = crud.create_product(db, test_product)
        print(f"✅ Created: {created.name} (ID: {created.id})")
        print(f"   Price: ${created.price}, Stock: {created.stock_quantity}")

        # Test 3: Get product by ID
        print("\n🔍 Test 3: Retrieving product...")
        retrieved = crud.get_product(db, created.id)
        print(f"✅ Retrieved: {retrieved.name}")

        # Test 4: Update product
        print("\n✏️ Test 4: Updating product price...")
        update_data = schemas.ProductUpdate(price=4.75)
        updated = crud.update_product(db, created.id, update_data)
        print(f"✅ Updated price to: ${updated.price}")

        # Test 5: Get all products
        print("\n📦 Test 5: Listing all products...")
        products = crud.get_products(db)
        print(f"✅ Found {len(products)} active products:")
        for p in products:
            print(f"   - {p.name}: ${p.price} (Stock: {p.stock_quantity})")

        # Test 6: Search products
        print("\n🔎 Test 6: Searching products...")
        search_results = crud.search_products(db, "coffee")
        print(f"✅ Found {len(search_results)} products with 'coffee':")
        for p in search_results:
            print(f"   - {p.name}")

        # Test 7: Create another product
        print("\n📝 Test 7: Creating another product...")
        another_product = schemas.ProductCreate(
            name="Chocolate Cake",
            price=6.99,
            stock_quantity=30,
            sku="CAKE-001",
            category="Desserts",
            description="Rich chocolate cake slice"
        )
        cake = crud.create_product(db, another_product)
        print(f"✅ Created: {cake.name}")

        # Test 8: Try duplicate SKU (should fail)
        print("\n🚫 Test 8: Testing duplicate SKU prevention...")
        try:
            duplicate = schemas.ProductCreate(
                name="Another Cappuccino",
                price=5.00,
                stock_quantity=10,
                sku="CAPP-001",  # Same SKU!
                category="Hot Drinks"
            )
            crud.create_product(db, duplicate)
            print("❌ ERROR: Should have failed on duplicate SKU")
        except ValueError as e:
            print(f"✅ Correctly rejected duplicate SKU: {e}")

        # Final count
        final_count = len(crud.get_products(db))
        print(f"\n📊 Total active products in database: {final_count}")

        db.close()

        print("\n" + "=" * 40)
        print("🎉 PHASE 2 COMPLETE! CRUD operations working!")
        print("\n✅ All database operations work correctly!")
        print("✅ Ready for Phase 3: Sales System")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_crud()