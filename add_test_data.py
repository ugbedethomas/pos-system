print("📝 Adding test data...")

try:
    from app.database import SessionLocal
    from app import crud, schemas

    db = SessionLocal()

    # Add some products
    products = [
        schemas.ProductCreate(
            name="Espresso",
            price=3.50,
            stock_quantity=100,
            sku="ESP-001",
            category="Coffee",
            description="Strong espresso shot"
        ),
        schemas.ProductCreate(
            name="Cappuccino",
            price=4.50,
            stock_quantity=80,
            sku="CAP-001",
            category="Coffee",
            description="Coffee with steamed milk foam"
        ),
        schemas.ProductCreate(
            name="Chocolate Cake",
            price=6.99,
            stock_quantity=30,
            sku="CAKE-001",
            category="Desserts",
            description="Rich chocolate cake slice"
        ),
        schemas.ProductCreate(
            name="Green Tea",
            price=2.99,
            stock_quantity=120,
            sku="TEA-001",
            category="Tea",
            description="Premium green tea"
        )
    ]

    for product in products:
        crud.create_product(db, product)

    print(f"✅ Added {len(products)} products")

    # Add a customer
    customer = crud.create_customer(db, schemas.CustomerCreate(
        name="John Doe",
        phone="123-456-7890",
        email="john@example.com"
    ))
    print(f"✅ Added customer: {customer.name}")

    db.close()
    print("\n🎉 Test data added successfully!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback

    traceback.print_exc()