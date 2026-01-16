#!/usr/bin/env python3
# render_build.py - Force Python 3.11 on Render
import os
import subprocess
import sys

print("🚀 Starting POS System Build on Render")
print(f"Python version: {sys.version}")

# Check if we need to install specific Python version
if "3.13" in sys.version:
    print("⚠️  Warning: Python 3.13 detected - may have SQLAlchemy issues")
    print("Trying to install SQLAlchemy 1.4.50...")

# Install dependencies
subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

print("✅ Build completed successfully!")