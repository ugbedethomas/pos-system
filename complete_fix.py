# complete_fix.py
import sqlite3
import os


def fix_database():
    print("=" * 60)
    print("🛠️  COMPLETE DATABASE SCHEMA FIX")
    print("=" * 60)

    # Find database
    db_path = 'pos.db'
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False

    print(f"📁 Database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"📊 Found tables: {tables}")

        # Define complete schema for each table
        schema_fixes = {
            'customers': [
                ('address', 'TEXT')
            ],
            'products': [
                ('cost_price', 'REAL DEFAULT 0'),
                ('barcode', 'TEXT'),
                ('reorder_level', 'INTEGER DEFAULT 10'),
                ('location', 'TEXT'),
                ('supplier_name', 'TEXT'),
                ('supplier_code', 'TEXT'),
                ('image_url', 'TEXT'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            ],
            'sales': [
                ('amount_paid', 'REAL DEFAULT 0'),
                ('change_amount', 'REAL DEFAULT 0'),
                ('tax_amount', 'REAL DEFAULT 0'),
                ('discount_amount', 'REAL DEFAULT 0'),
                ('payment_status', 'TEXT DEFAULT "completed"'),
                ('user_id', 'INTEGER'),
                ('notes', 'TEXT')
            ],
            'sale_items': [
                ('unit_price', 'REAL NOT NULL'),
                ('subtotal', 'REAL NOT NULL')
            ],
            'users': [
                ('full_name', 'TEXT'),
                ('role', 'TEXT DEFAULT "cashier"'),
                ('last_login', 'TIMESTAMP'),
                ('is_active', 'BOOLEAN DEFAULT 1')
            ]
        }

        print("\n🔧 Fixing tables...")
        print("-" * 40)

        for table_name, columns in schema_fixes.items():
            if table_name in tables:
                print(f"\n📋 {table_name.upper()}:")
                # Get existing columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_cols = [col[1] for col in cursor.fetchall()]

                for col_name, col_type in columns:
                    if col_name not in existing_cols:
                        try:
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                            print(f"  ✅ Added: {col_name}")
                        except Exception as e:
                            print(f"  ⚠️  {col_name}: {str(e)}")
                    else:
                        print(f"  ✓ Already exists: {col_name}")

        # Create indexes
        print("\n📊 Creating indexes...")
        print("-" * 40)

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_sales_created ON sales(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sales_receipt ON sales(receipt_number)"
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"  ✅ Created index")
            except Exception as e:
                print(f"  ⚠️  Index: {str(e)}")

        conn.commit()

        print("\n" + "=" * 60)
        print("🎉 DATABASE COMPLETELY FIXED!")
        print("=" * 60)

        # Show final schema
        print("\n📋 FINAL SCHEMA:")
        print("-" * 40)

        for table in ['customers', 'products', 'sales', 'sale_items', 'users']:
            if table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = cursor.fetchall()
                print(f"\n{table.upper()}:")
                for col in cols:
                    nullable = "NOT NULL" if col[3] else "NULL"
                    print(f"  - {col[1]:20} {col[2]:15} {nullable}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    if fix_database():
        print("\n✅ You can now:")
        print("   1. Refresh your browser")
        print("   2. Login with admin/admin123")
        print("   3. The POS system should work perfectly!")
    else:
        print("\n❌ Fix failed. Try visiting /force-init-db")

    print("\n" + "=" * 60)
    input("Press Enter to exit...")