#!/bin/bash
# One-click build script for InsightPilot (Linux/Mac)

set -e

echo "Building InsightPilot!"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment!"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment!"
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip!"
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies!"
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies!"
pip install -e ".[dev]"

# Run tests
echo "Running tests!"
python -m pytest tests/ -v

# Build executable with PyInstaller
echo "Building executable!"
pyinstaller --onefile --windowed --name InsightPilot src/main.py

# Copy assets to dist folder
if [ -d "assets" ]; then
    echo "Copying assets!"
    cp -r assets dist/
fi

echo
echo "Build completed successfully!"
echo "Executable location: dist/InsightPilot"
echo

# Make executable
chmod +x dist/InsightPilot
