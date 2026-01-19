# fix_all_min_stock.py
import os

print("=" * 60)
print("🛠️  Fixing ALL min_stock_level references")
print("=" * 60)

crud_path = 'app/crud.py'
if not os.path.exists(crud_path):
    print(f"❌ Could not find {crud_path}")
    exit(1)

with open(crud_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Count how many times min_stock_level appears
count = content.count('min_stock_level')
print(f"Found {count} occurrences of 'min_stock_level'")

if count > 0:
    # Replace ALL occurrences
    new_content = content.replace('min_stock_level', 'reorder_level')

    with open(crud_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Replaced ALL 'min_stock_level' with 'reorder_level'")
else:
    print("✅ No 'min_stock_level' found - already fixed!")

# Also check database
print("\n📝 Checking database schema...")
try:
    import sqlite3

    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()

    # Check what columns exist
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'min_stock_level' in columns:
        print("⚠️ Database has 'min_stock_level' column")
        print("   You can rename it or leave it - code uses 'reorder_level' now")

    if 'reorder_level' in columns:
        print("✅ Database has 'reorder_level' column")
    else:
        print("❌ Database missing 'reorder_level' column")
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN reorder_level INTEGER DEFAULT 10")
            print("✅ Added 'reorder_level' column to database")
        except Exception as e:
            print(f"⚠️ Could not add column: {e}")

    conn.commit()
    conn.close()
except Exception as e:
    print(f"⚠️ Database check: {e}")

print("\n" + "=" * 60)
print("🎉 Fix complete! Restart your server.")
print("=" * 60)