print("Checking files...")
import os

files = ["requirements.txt", "runtime.txt", "gunicorn_config.py", "render.yaml", 
         "setup_database.py", ".gitignore", "Procfile", "wsgi.py", "README.md"]

for file in files:
    if os.path.exists(file):
        print(f"✓ {file}")
    else:
        print(f"✗ {file} - MISSING")

print("\nChecking app files...")
app_files = ["app/database.py", "app/models.py", "web_server.py"]
for file in app_files:
    if os.path.exists(file):
        print(f"✓ {file}")
    else:
        print(f"✗ {file} - MISSING")
