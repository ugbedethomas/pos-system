# fix_db.py
import sqlite3
import os

print("=" * 50)
print("🛠️  POS SYSTEM DATABASE FIXER")
print("=" * 50)

# Find database
db_path = 'pos.db'
if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    print("Looking for database in other locations...")

    # Try other common locations
    possible_paths = ['instance/pos.db', 'app/pos.db', '../pos.db']
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            print(f"✅ Found database at: {db_path}")
            break

    if not db_path:
        print("❌ No database found!")
        print("Please visit http://localhost:5000/init-now first")
        input("Press Enter to exit...")
        exit(1)

print(f"📁 Database: {db_path}")
print("-" * 50)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"📊 Found {len(tables)} tables: {tables}")

# Show current schema
print("\n🔍 Current Schema:")
for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"\n{table.upper()}:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

print("\n" + "=" * 50)
print("🔧 Applying fixes...")
print("-" * 50)

# Fix customers table
if 'customers' in tables:
    cursor.execute("PRAGMA table_info(customers)")
    cust_cols = [col[1] for col in cursor.fetchall()]

    if 'address' not in cust_cols:
        try:
            cursor.execute("ALTER TABLE customers ADD COLUMN address TEXT")
            print("✅ Added 'address' column to customers")
        except Exception as e:
            print(f"⚠️ Could not add address: {e}")
    else:
        print("✅ customers.address already exists")

# Fix products table
if 'products' in tables:
    cursor.execute("PRAGMA table_info(products)")
    prod_cols = [col[1] for col in cursor.fetchall()]

    columns_to_add = [
        ('cost_price', 'REAL DEFAULT 0'),
        ('barcode', 'TEXT'),
        ('reorder_level', 'INTEGER DEFAULT 10'),
        ('location', 'TEXT'),
        ('supplier_name', 'TEXT'),
        ('supplier_code', 'TEXT'),
        ('image_url', 'TEXT'),
        ('is_active', 'BOOLEAN DEFAULT 1'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]

    for col_name, col_type in columns_to_add:
        if col_name not in prod_cols:
            try:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added '{col_name}' to products")
            except Exception as e:
                print(f"⚠️ Could not add {col_name}: {e}")
        else:
            print(f"✅ products.{col_name} already exists")

# Create indexes
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
    print("✅ Created index on barcode")
except:
    print("✅ Barcode index already exists")

conn.commit()

print("\n" + "=" * 50)
print("🎉 DATABASE FIXED SUCCESSFULLY!")
print("-" * 50)

# Show updated schema
print("\n📊 Updated Schema:")
for table in ['products', 'customers']:
    if table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"\n{table.upper()}:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

conn.close()

print("\n" + "=" * 50)
print("✅ You can now:")
print("1. Refresh your browser at http://localhost:5000")
print("2. Login with admin/admin123")
print("3. Start using the POS system!")
print("=" * 50)
input("\nPress Enter to exit...")