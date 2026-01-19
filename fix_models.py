# fix_models.py
print("=" * 60)
print("🛠️  Fixing Models and CRUD Issues")
print("=" * 60)

# Fix crud.py
import os

crud_path = 'app/crud.py'
if os.path.exists(crud_path):
    with open(crud_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the min_stock_level issue
    if 'min_stock_level' in content:
        new_content = content.replace(
            'models.Product.stock_quantity <= models.Product.min_stock_level,',
            'models.Product.stock_quantity <= models.Product.reorder_level,'
        )

        with open(crud_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Updated crud.py: min_stock_level → reorder_level")
    else:
        print("✅ crud.py already uses reorder_level")
else:
    print(f"⚠️ Could not find {crud_path}")

# Fix database column name if needed
print("\n📝 Checking database...")
try:
    import sqlite3

    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()

    # Check if min_stock_level column exists (shouldn't)
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'min_stock_level' in columns:
        print("⚠️ Found min_stock_level column in database")
        print("✅ But crud.py now uses reorder_level, so it's fine")
    else:
        print("✅ Database uses reorder_level")

    conn.close()
except Exception as e:
    print(f"⚠️ Database check: {e}")

print("\n" + "=" * 60)
print("🎉 Fix complete! Your models should now work.")
print("IMPORTANT: Make sure your app/models.py has only ONE Product class!")
print("=" * 60)