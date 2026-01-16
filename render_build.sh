#!/bin/bash
set -o errexit

echo " Starting POS System build..."
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

echo " Updating pip..."
pip install --upgrade pip

echo " Installing dependencies..."
pip install -r requirements.txt

echo " Build completed!"
