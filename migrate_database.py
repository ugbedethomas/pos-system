# migrate_database.py
import sqlite3
import os
import sys
from datetime import datetime


def check_and_migrate_database():
    """Check database schema and migrate if needed"""
    print("🔍 Checking database schema...")

    # Try to find database file
    possible_db_paths = ['pos.db', 'app/pos.db', 'instance/pos.db']
    db_path = None

    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            print(f"✅ Found database at: {db_path}")
            break

    if not db_path:
        print("❌ No database file found!")
        print("Please visit /init-now in your browser first")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            print("❌ Products table doesn't exist!")
            print("Please visit /init-now in your browser first")
            conn.close()
            return False

        # Get current columns in products table
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"📊 Current columns in products table: {column_names}")

        # Define required columns and their types
        required_columns = {
            'id': 'INTEGER PRIMARY KEY',
            'name': 'TEXT NOT NULL',
            'description': 'TEXT',
            'price': 'REAL NOT NULL',
            'cost_price': 'REAL DEFAULT 0',
            'stock_quantity': 'INTEGER DEFAULT 0',
            'category': 'TEXT',
            'sku': 'TEXT UNIQUE',
            'barcode': 'TEXT',
            'reorder_level': 'INTEGER DEFAULT 10',
            'location': 'TEXT',
            'supplier_name': 'TEXT',
            'supplier_code': 'TEXT',
            'image_url': 'TEXT',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP',
            'is_active': 'BOOLEAN DEFAULT 1'
        }

        # Check and add missing columns
        added_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in column_names:
                try:
                    # Skip id column if it's the primary key
                    if col_name == 'id':
                        continue

                    print(f"➕ Adding missing column: {col_name} ({col_type})")
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
                    added_columns.append(col_name)
                except Exception as e:
                    print(f"⚠️ Could not add column {col_name}: {e}")

        # Create indexes for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
            print("✅ Created index on barcode column")
        except Exception as e:
            print(f"⚠️ Could not create index: {e}")

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")
            print("✅ Created index on sku column")
        except Exception as e:
            print(f"⚠️ Could not create index: {e}")

        conn.commit()

        if added_columns:
            print(f"\n🎉 Successfully added {len(added_columns)} columns: {added_columns}")
            print("\n🔧 Migration completed successfully!")
        else:
            print("\n✅ Database schema is already up to date!")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def quick_fix_get_products():
    """Create a temporary fix for get_products function"""
    fix_code = '''
# TEMPORARY FIX for crud.py - Add this at the top of get_products function
def get_products(db, skip: int = 0, limit: int = 100):
    """Get products with fallback for missing columns"""
    try:
        # Try the normal query first
        return db.query(models.Product).filter(models.Product.is_active == True).offset(skip).limit(limit).all()
    except Exception as e:
        # If there's a schema error, try without is_active filter
        print(f"⚠️ Schema error in get_products, using fallback: {e}")
        try:
            return db.query(models.Product).offset(skip).limit(limit).all()
        except Exception:
            # If that fails too, use raw SQL
            result = db.execute("SELECT * FROM products LIMIT :limit OFFSET :skip", 
                              {"limit": limit, "skip": skip})
            return result.fetchall()
'''
    print("\n📝 If migration doesn't work, add this to your crud.py:")
    print(fix_code)


if __name__ == '__main__':
    print("=" * 60)
    print("🔄 POS SYSTEM DATABASE MIGRATION TOOL")
    print("=" * 60)

    success = check_and_migrate_database()

    if not success:
        print("\n🚨 MIGRATION FAILED - TRY THESE OPTIONS:")
        print("1. Visit http://localhost:5000/init-now to initialize fresh database")
        print("2. Visit http://localhost:5000/force-init-db to force recreate (WARNING: LOSES DATA)")
        print("3. Check if you have write permissions to the database file")

    print("\n" + "=" * 60)
    input("Press Enter to exit...")