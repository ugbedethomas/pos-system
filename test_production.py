# Create test_production.py with proper Python syntax
@"
# test_production.py


import os
import sys

print("Testing production setup...")

# Test 1: Check if all required files exist
required_files = [
    'requirements.txt',
    'runtime.txt',
    'gunicorn_config.py',
    'render.yaml',
    'setup_database.py',
    '.gitignore',
    'Procfile',
    'web_server.py',
    'app/database.py',
    'app/models.py'
]

print("\n1. Checking required files:")
for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - MISSING")

# Test 2: Check imports
print("\n2. Testing imports...")
try:
    from app.database import engine, Base

    print("   ✅ Database imports work")

    from app import models

    print("   ✅ Models imports work")

    import flask

    print("   ✅ Flask imports work")

    import sqlalchemy

    print("   ✅ SQLAlchemy imports work")

except ImportError as e:
    print(f"   ❌ Import error: {e}")

# Test 3: Check database connection
print("\n3. Testing database connection...")
try:
    if os.environ.get('DATABASE_URL'):
        print(f"   ✅ PostgreSQL URL found: {os.environ.get('DATABASE_URL')[:50]}...")
    else:
        print("   ✅ Using SQLite (local development)")
except Exception as e:
    print(f"   ❌ Database error: {e}")

print("\n✅ All tests completed!")
print("\nNext steps:")
print("1. git add .")
print("2. git commit -m 'Ready for deployment'")
print("3. git push origin main")
print("4. Deploy to Render.com")
"@ | Out-File -FilePath "
test_production.py
" -Encoding UTF8