@echo off
REM One-click build for InsightPilot (Windows)

echo Building InsightPilot v0.0.1-nightly (POC)!
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment!
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment!
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip!
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies!
pip install -r requirements.txt

REM Install development dependencies
echo Installing development dependencies!
REM Development dependencies are already included in requirements.txt

REM Run tests
echo Running tests!
python -m pytest tests/ -v
if errorlevel 1 (
    echo ERROR: Tests failed
    pause
    exit /b 1
)

REM Build executable with PyInstaller
echo Building executable!
pyinstaller InsightPilot.spec

REM Copy assets to dist folder
if exist "assets" (
    echo Copying assets!
    xcopy assets dist\assets\ /s /i /y
)

echo.
echo Build completed successfully!
echo Executable location: dist\InsightPilot.exe

