#!/usr/bin/env python3
# scripts/simple_backup.py - Simple backup script for Windows
import json
from datetime import datetime
import os
from pathlib import Path


def create_simple_backup():
    """Create a simple backup file with deployment info"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'message': 'Pre-deployment backup',
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'has_database_url': bool(os.environ.get('DATABASE_URL'))
        }

        backup_filename = backup_dir / f"deploy_backup_{timestamp}.json"

        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)

        print(f"✅ Backup info saved to: {backup_filename}")

        # Save as latest
        latest_backup = backup_dir / "latest_deploy_backup.json"
        with open(latest_backup, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)

        return str(backup_filename)

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None


if __name__ == "__main__":
    create_simple_backup()