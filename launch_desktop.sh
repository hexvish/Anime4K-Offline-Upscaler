#!/bin/bash

# Kill any existing processes on port 5000 (cross-platform way)
if command -v lsof >/dev/null 2>&1; then
    lsof -ti:5000 | xargs kill -9 >/dev/null 2>&1 || true
elif command -v fuser >/dev/null 2>&1; then
    fuser -k 5000/tcp 2>/dev/null || true
fi

# Set environment variables (Linux-specific fixes)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export QT_QPA_PLATFORM=xcb
    export QTWEBENGINE_DISABLE_SANDBOX=1
    export QTWEBENGINE_CHROME_FLAGS="--no-sandbox --disable-gpu-sandbox --enable-webgl --ignore-gpu-blocklist"
fi

# Activate virtual environment and run
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 app.py
else
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi
