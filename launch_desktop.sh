#!/bin/bash

# Kill any existing processes on port 5000
fuser -k 5000/tcp 2>/dev/null || true

# Set environment variables for Linux stability
export QT_QPA_PLATFORM=xcb
export QTWEBENGINE_DISABLE_SANDBOX=1
export QTWEBENGINE_CHROME_FLAGS="--no-sandbox --disable-gpu-sandbox --enable-webgl --ignore-gpu-blocklist"

# Activate virtual environment and run
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 app.py
else
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi
