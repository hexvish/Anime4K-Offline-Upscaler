@echo off
setlocal

echo 🎬 Anime4K-Offline-Upscaler: Unified Launcher
echo ==============================================

:: --- SETUP PHASE ---

if not exist venv (
    echo 📋 First-time setup detected...
    
    :: 1. Check Python
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python is not installed or not in PATH.
        echo Please install Python 3.11+ from python.org
        pause
        exit /b 1
    )
    echo ✅ Python found
    
    :: 2. Create Virtual Environment
    echo 📦 Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    :: 3. Install Dependencies
    echo 📦 Installing dependencies...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    :: 4. Create Directories
    echo 📁 Creating application directories...
    if not exist uploads mkdir uploads
    if not exist outputs mkdir outputs
    if not exist bin mkdir bin
    
    echo ✅ Setup complete!
    echo ---------------------------
) else (
    :: Activate if venv exists
    call venv\Scripts\activate.bat
)

:: --- RUN PHASE ---

echo 🚀 Launching application...
python app.py

if %errorlevel% neq 0 (
    echo ❌ Application exited with an error.
    pause
)
