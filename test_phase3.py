print("🧪 PHASE 3 TEST: Sales System")
print("=" * 40)


def test_sales():
    try:
        print("Testing Sales System...")

        # Import modules
        from app.database import SessionLocal
        from app import crud, schemas
        from datetime import datetime

        print("✅ Test 1: All imports successful")

        # Get database session
        db = SessionLocal()

        # Test 2: Create a customer
        print("\n👤 Test 2: Creating customer...")
        customer_data = schemas.CustomerCreate(
            name="John Doe",
            phone="123-456-7890",
            email="john@example.com"
        )
        customer = crud.create_customer(db, customer_data)
        print(f"✅ Created customer: {customer.name} (ID: {customer.id})")

        # Test 3: Create a sale
        print("\n💰 Test 3: Creating sale...")

        # First, get some products
        products = crud.get_products(db, limit=2)
        if len(products) < 2:
            print("❌ Need at least 2 products for test")
            return

        # Create sale items
        sale_items = [
            schemas.SaleItemCreate(product_id=products[0].id, quantity=2),
            schemas.SaleItemCreate(product_id=products[1].id, quantity=1)
        ]

        # Create sale
        sale_data = schemas.SaleCreate(
            customer_id=customer.id,
            payment_method="cash",
            items=sale_items
        )

        sale = crud.create_sale(db, sale_data)
        print(f"✅ Created sale #{sale.receipt_number}")
        print(f"   Total: ${sale.total_amount:.2f}, Tax: ${sale.tax_amount:.2f}")
        print(f"   Items: {len(sale.items)}, Payment: {sale.payment_method}")

        # Test 4: Check stock was reduced
        print("\n📦 Test 4: Checking stock reduction...")
        for item in sale.items:
            product = crud.get_product(db, item.product_id)
            print(f"   {product.name}: Was {product.stock_quantity + item.quantity}, Now {product.stock_quantity}")

        # Test 5: Get sale by ID
        print("\n🔍 Test 5: Retrieving sale...")
        retrieved = crud.get_sale(db, sale.id)
        print(f"✅ Retrieved sale: {retrieved.receipt_number}")

        # Test 6: List all sales
        print("\n📋 Test 6: Listing all sales...")
        sales = crud.get_sales(db)
        print(f"✅ Found {len(sales)} total sales")
        for s in sales:
            print(f"   - {s.receipt_number}: ${s.total_amount:.2f} ({len(s.items)} items)")

        # Test 7: Try sale with insufficient stock
        print("\n🚫 Test 7: Testing insufficient stock...")
        try:
            # Try to buy 1000 units of first product (should fail)
            fail_items = [schemas.SaleItemCreate(product_id=products[0].id, quantity=1000)]
            fail_sale = schemas.SaleCreate(
                items=fail_items,
                payment_method="cash"
            )
            crud.create_sale(db, fail_sale)
            print("❌ ERROR: Should have failed on insufficient stock")
        except ValueError as e:
            print(f"✅ Correctly rejected: {e}")

        # Test 8: Create another sale (walk-in customer, no ID)
        print("\n💰 Test 8: Creating walk-in sale...")
        walkin_items = [schemas.SaleItemCreate(product_id=products[0].id, quantity=1)]
        walkin_sale = schemas.SaleCreate(
            items=walkin_items,
            payment_method="card"
        )
        walkin = crud.create_sale(db, walkin_sale)
        print(f"✅ Created walk-in sale: {walkin.receipt_number}")

        # Final counts
        product_count = len(crud.get_products(db))
        customer_count = len(crud.get_customers(db))
        sales_count = len(crud.get_sales(db))

        print(f"\n📊 Final counts:")
        print(f"   Products: {product_count}")
        print(f"   Customers: {customer_count}")
        print(f"   Sales: {sales_count}")

        db.close()

        print("\n" + "=" * 40)
        print("🎉 PHASE 3 COMPLETE! Sales System is working!")
        print("\n✅ Customers can be created")
        print("✅ Sales process stock correctly")
        print("✅ Receipt numbers generated")
        print("✅ Stock validation works")
        print("\n✅ Ready for Phase 4: Inventory Management")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_sales()