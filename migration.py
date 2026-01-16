# migration.py - Save this in the same folder as web_server.py
import mysql.connector
from mysql.connector import Error
import getpass


def run_migration():
    try:
        print("=" * 50)
        print("DATABASE MIGRATION TOOL")
        print("=" * 50)

        # Get database credentials
        print("\n📋 Enter database credentials:")
        host = input("Host [localhost]: ") or "localhost"
        user = input("Username [root]: ") or "root"
        password = getpass.getpass("Password (input hidden): ")
        database = input("Database name [pos_system]: ") or "pos_system"

        # Database configuration
        db_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }

        # Test connection
        print("\n🔌 Testing database connection...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        print("✅ Connected to database successfully!")

        # Check current state
        print("\n📊 Checking current database state...")
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Found {len(tables)} tables: {', '.join(tables)}")

        # Check sales table structure
        cursor.execute("DESCRIBE sales")
        sales_columns = [col[0] for col in cursor.fetchall()]
        print(f"\nSales table has {len(sales_columns)} columns")

        # List of migrations to run
        migrations = []

        # Check and add missing columns
        if 'user_id' not in sales_columns:
            migrations.append("ALTER TABLE sales ADD COLUMN user_id INTEGER NOT NULL AFTER receipt_number")
            print("  ➕ Will add: user_id column")

        if 'subtotal' not in sales_columns:
            migrations.append("ALTER TABLE sales ADD COLUMN subtotal FLOAT DEFAULT 0 AFTER customer_id")
            print("  ➕ Will add: subtotal column")

        if 'amount_paid' not in sales_columns:
            migrations.append("ALTER TABLE sales ADD COLUMN amount_paid FLOAT NOT NULL DEFAULT 0 AFTER discount_amount")
            print("  ➕ Will add: amount_paid column")

        if 'change_given' not in sales_columns:
            migrations.append("ALTER TABLE sales ADD COLUMN change_given FLOAT DEFAULT 0 AFTER amount_paid")
            print("  ➕ Will add: change_given column")

        # Check foreign key
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'sales' 
            AND COLUMN_NAME = 'user_id' 
            AND CONSTRAINT_NAME != 'PRIMARY'
        """)
        if not cursor.fetchone():
            migrations.append(
                "ALTER TABLE sales ADD CONSTRAINT fk_sales_user FOREIGN KEY (user_id) REFERENCES users(id)")
            print("  ➕ Will add: foreign key constraint")

        # Check inventory_logs table
        if 'inventory_logs' not in tables:
            migrations.append("""
                CREATE TABLE inventory_logs (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    product_id INT NOT NULL,
                    previous_stock INT DEFAULT 0,
                    new_stock INT DEFAULT 0,
                    change_type VARCHAR(20),
                    order_id INT,
                    user_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            print("  ➕ Will create: inventory_logs table")

        if not migrations:
            print("\n✅ No migrations needed. Database is up to date!")
            return

        # Ask for confirmation
        print(f"\n⚠️  {len(migrations)} migrations will be executed.")
        confirm = input("Do you want to proceed? (yes/no): ").lower()

        if confirm not in ['yes', 'y']:
            print("❌ Migration cancelled.")
            return

        # Execute migrations
        print("\n🚀 Executing migrations...")
        for i, migration in enumerate(migrations, 1):
            try:
                print(f"\n[{i}/{len(migrations)}] Executing...")
                cursor.execute(migration)
                print(f"   ✅ Success")
            except Error as e:
                print(f"   ⚠️  Skipped (might already exist): {e}")
                continue

        # Commit changes
        connection.commit()
        print("\n" + "=" * 50)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 50)

        # Show final state
        print("\n📋 FINAL DATABASE STATE:")

        cursor.execute("DESCRIBE sales")
        print("\nSales table structure:")
        for column in cursor.fetchall():
            print(
                f"  - {column[0]:15} {column[1]:20} {'NULL' if column[2] == 'YES' else 'NOT NULL':10} {str(column[4] or ''):10}")

        cursor.execute("SHOW TABLES")
        print(f"\nTotal tables: {len(cursor.fetchall())}")

    except Error as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPossible solutions:")
        print("1. Check if MySQL is running: sudo service mysql start (Linux/Mac) or start MySQL service (Windows)")
        print("2. Check database credentials")
        print("3. Make sure the database 'pos_system' exists")
        print("4. Check if you have permission to modify the database")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔒 Database connection closed")


def quick_migration():
    """Quick migration without prompts"""
    try:
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',  # Your password here
            'database': 'pos_system'
        }

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        print("🚀 Running quick migration...")

        migrations = [
            "ALTER TABLE sales ADD COLUMN user_id INTEGER NOT NULL AFTER receipt_number",
            "ALTER TABLE sales ADD COLUMN subtotal FLOAT DEFAULT 0 AFTER customer_id",
            "ALTER TABLE sales ADD COLUMN amount_paid FLOAT NOT NULL DEFAULT 0 AFTER discount_amount",
            "ALTER TABLE sales ADD COLUMN change_given FLOAT DEFAULT 0 AFTER amount_paid",
            "ALTER TABLE sales ADD CONSTRAINT fk_sales_user FOREIGN KEY (user_id) REFERENCES users(id)",
            """
            CREATE TABLE IF NOT EXISTS inventory_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                product_id INT NOT NULL,
                previous_stock INT DEFAULT 0,
                new_stock INT DEFAULT 0,
                change_type VARCHAR(20),
                order_id INT,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        ]

        for migration in migrations:
            try:
                cursor.execute(migration)
                print("✅ Migration executed")
            except Error as e:
                print(f"⚠️  Skipped: {e}")

        connection.commit()
        print("\n✅ Quick migration completed!")

    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("Choose migration method:")
    print("1. Interactive migration (recommended)")
    print("2. Quick migration (uses default credentials)")

    choice = input("Enter choice (1 or 2): ")

    if choice == "1":
        run_migration()
    elif choice == "2":
        quick_migration()
    else:
        print("Invalid choice")