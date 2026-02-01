@echo off
setlocal

echo 🎬 Anime4K-Offline-Upscaler - Windows Setup
echo ===========================================

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)
echo ✅ Python found

:: Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FFmpeg is not installed or not in PATH.
    echo Please install FFmpeg with libplacebo support.
    pause
    exit /b 1
)
echo ✅ FFmpeg found

:: Check libplacebo support
ffmpeg -filters 2>&1 | findstr "libplacebo" >nul
if %errorlevel% neq 0 (
    echo ⚠️  Warning: FFmpeg may not have libplacebo support.
    echo You may need a build of FFmpeg that includes libplacebo.
)

:: Create virtual environment
echo.
echo 📦 Creating virtual environment...
python -m venv venv

:: Activate and install
call venv\Scripts\activate.bat

echo 📦 Upgrading pip...
python -m pip install --upgrade pip

echo 📦 Installing Python dependencies...
pip install -r requirements.txt

:: Create directories
echo 📁 Creating directories...
if not exist uploads mkdir uploads
if not exist outputs mkdir outputs
if not exist shaders mkdir shaders

echo.
echo ✅ Setup complete!
echo.
echo To start the server:
echo   launch_desktop.bat
echo.
pause
