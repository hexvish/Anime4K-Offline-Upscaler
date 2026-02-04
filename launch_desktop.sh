#!/bin/bash
set -e

# ==========================================
# Anime4K-Offline-Upscaler: Unified Launcher
# ==========================================

echo "🎬 Anime4K-Offline-Upscaler"

# --- HELPER FUNCTIONS ---

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "📦 Attempting to install via Homebrew..."
            if command -v brew &> /dev/null; then
                brew install python
            else
                echo "❌ Homebrew not found. Install it from https://brew.sh/ or install Python manually from python.org."
                exit 1
            fi
        else
            echo "Please install Python 3.10+ manually for your Linux distribution."
            exit 1
        fi
    fi
}

check_ffmpeg() {
    if ! command -v ffmpeg &> /dev/null; then
        echo "⚠️  System FFmpeg not found."
        echo "   The application will handle downloading a local copy automatically."
    fi
}

# --- SETUP PHASE ---

if [ ! -d "venv" ]; then
    echo "📋 First-time setup detected..."
    
    # 1. Check System Dependencies
    check_python
    check_ffmpeg
    
    # 2. Create Virtual Environment
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    # 3. Install Python Dependencies
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 4. Create Directories
    echo "📁 Creating application directories..."
    mkdir -p uploads outputs bin

    echo "✅ Setup complete!"
    echo "-----------------------------"
else
    # Just activate if venv exists
    source venv/bin/activate
fi

# --- RUN PHASE ---

# Kill any existing processes (Linux/macOS)
if command -v lsof >/dev/null 2>&1; then
    lsof -ti:5000 | xargs kill -9 >/dev/null 2>&1 || true
elif command -v fuser >/dev/null 2>&1; then
    fuser -k 5000/tcp 2>/dev/null || true
fi

# Linux-specific fixes
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export QT_QPA_PLATFORM=xcb
    export QTWEBENGINE_DISABLE_SANDBOX=1
    export QTWEBENGINE_CHROME_FLAGS="--no-sandbox --disable-gpu-sandbox --enable-webgl --ignore-gpu-blocklist"
fi

echo "🚀 Launching application..."
python3 app.py
