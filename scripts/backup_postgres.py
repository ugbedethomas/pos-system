#!/usr/bin/env python3
# scripts/backup_postgres.py - PostgreSQL backup script for Render
import os
import json
from datetime import datetime
import sys
from pathlib import Path


def backup_postgresql():
    """Backup PostgreSQL database from Render"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ No DATABASE_URL found")
            return None

        print("📦 Backing up PostgreSQL database...")

        # Parse database URL
        from urllib.parse import urlparse
        result = urlparse(database_url)

        # Extract connection details
        dbname = result.path[1:] if result.path.startswith('/') else result.path
        user = result.username
        password = result.password
        host = result.hostname
        port = result.port or 5432

        print(f"  Database: {dbname}")
        print(f"  Host: {host}")

        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
            return None

        # Connect to database
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require'
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)

        tables = [row['table_name'] for row in cursor.fetchall()]

        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'database': dbname,
            'tables': {}
        }

        # Backup each table
        for table in tables:
            print(f"  📊 Backing up table: {table}")
            cursor.execute(f'SELECT * FROM "{table}"')
            rows = cursor.fetchall()
            backup_data['tables'][table] = rows

        cursor.close()
        conn.close()

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        backup_filename = backup_dir / f"postgres_backup_{timestamp}.json"

        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, default=str)

        print(f"✅ Backup saved to: {backup_filename}")

        # Copy to latest backup
        latest_backup = backup_dir / "latest_postgres_backup.json"
        try:
            import shutil
            shutil.copy2(backup_filename, latest_backup)
            print(f"💾 Latest backup saved as: {latest_backup}")
        except Exception as e:
            print(f"⚠️  Could not save latest backup: {e}")

        return str(backup_filename)

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    backup_file = backup_postgresql()
    sys.exit(0 if backup_file else 1)