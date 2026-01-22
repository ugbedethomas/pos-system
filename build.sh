#!/bin/bash
set -o errexit

# Install specific Python version compatibility packages
pip install --upgrade pip
pip install -r requirements.txt
