@echo off
setlocal

echo 🎬 Launching Anime4K-Offline-Upscaler...

:: Check for venv
if not exist venv\Scripts\activate.bat (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: Activate and run
call venv\Scripts\activate.bat
python app.py

if %errorlevel% neq 0 (
    echo ❌ Application exited with an error.
    pause
)
