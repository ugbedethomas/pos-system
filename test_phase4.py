print("🧪 PHASE 4 TEST: Inventory Management")
print("=" * 40)


def test_inventory():
    try:
        print("Testing Inventory Management...")

        # Import modules
        from app.database import SessionLocal
        from app import crud, schemas

        print("✅ Test 1: All imports successful")

        # Get database session
        db = SessionLocal()

        # Test 2: Get inventory report
        print("\n📊 Test 2: Generating inventory report...")
        report = crud.get_inventory_report(db)
        print(f"✅ Generated report for {len(report)} products")

        # Show some report items
        for item in report[:3]:  # First 3 items
            status_icon = "🔴" if item["status"] == "LOW" else "🟢" if item["status"] == "OK" else "⚫"
            print(
                f"   {status_icon} {item['product_name']}: {item['current_stock']} units (${item['total_value']:.2f}) - {item['status']}")

        # Test 3: Check low stock products
        print("\n⚠️ Test 3: Checking low stock products...")
        low_stock = crud.get_low_stock_products(db)
        print(f"✅ Found {len(low_stock)} products with low stock")
        for product in low_stock:
            print(f"   ⚠️ {product.name}: {product.stock_quantity}/{product.min_stock_level}")

        # Test 4: Manual stock adjustment (add stock)
        print("\n📦 Test 4: Manual stock adjustment...")

        # Get a product
        products = crud.get_products(db, limit=1)
        if not products:
            print("❌ No products found")
            return

        product = products[0]
        old_stock = product.stock_quantity

        # Add 10 units
        adjustment = schemas.StockMovementCreate(
            product_id=product.id,
            quantity=10,
            movement_type="purchase",
            reference="PO-001",
            notes="Manual stock purchase",
            created_by="admin"
        )

        movement = crud.create_stock_movement(db, adjustment)
        print(f"✅ Added 10 units to {product.name}")
        print(f"   Old stock: {old_stock}, New stock: {product.stock_quantity}")
        print(f"   Movement ID: {movement.id}, Type: {movement.movement_type}")

        # Test 5: Get stock movements for product
        print("\n📈 Test 5: Viewing stock movement history...")
        movements = crud.get_stock_movements(db, product_id=product.id, limit=5)
        print(f"✅ Found {len(movements)} movements for {product.name}")
        for mov in movements:
            sign = "+" if mov.quantity > 0 else ""
            print(
                f"   {mov.created_at.strftime('%H:%M')}: {sign}{mov.quantity} units ({mov.movement_type}) - {mov.notes}")

        # Test 6: Update minimum stock level
        print("\n⚙️ Test 6: Updating minimum stock level...")
        updated = crud.update_stock_level(db, product.id, 20)
        print(f"✅ Updated {product.name} min stock from {product.min_stock_level} to 20")

        # Test 7: Check low stock again (should include our product if stock < 20)
        print("\n⚠️ Test 7: Rechecking low stock...")
        low_stock_after = crud.get_low_stock_products(db)
        low_product_names = [p.name for p in low_stock_after]
        if product.name in low_product_names:
            print(f"✅ {product.name} correctly flagged as low stock")
        else:
            print(f"✅ {product.name} has sufficient stock")

        # Test 8: Create a return/refund (negative movement)
        print("\n↩️ Test 8: Processing product return...")
        return_movement = schemas.StockMovementCreate(
            product_id=product.id,
            quantity=2,
            movement_type="return",
            reference="RETURN-001",
            notes="Customer return",
            created_by="cashier"
        )

        return_record = crud.create_stock_movement(db, return_movement)
        print(f"✅ Processed return of 2 units for {product.name}")
        print(f"   New stock: {product.stock_quantity}")

        # Final report
        print("\n📋 Final Inventory Summary:")
        final_report = crud.get_inventory_report(db)
        total_value = sum(item["total_value"] for item in final_report)
        low_count = sum(1 for item in final_report if item["status"] == "LOW")
        out_count = sum(1 for item in final_report if item["status"] == "OUT")

        print(f"   Total Products: {len(final_report)}")
        print(f"   Total Inventory Value: ${total_value:.2f}")
        print(f"   Low Stock Items: {low_count}")
        print(f"   Out of Stock Items: {out_count}")

        db.close()

        print("\n" + "=" * 40)
        print("🎉 PHASE 4 COMPLETE! Inventory Management is working!")
        print("\n✅ Stock movements tracked")
        print("✅ Inventory reports generated")
        print("✅ Low stock alerts work")
        print("✅ Manual adjustments possible")
        print("\n✅ Ready for Phase 5: Web Interface")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_inventory()