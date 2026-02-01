#!/bin/bash
set -e

echo "🎬 Anime4K Web Upscaler - Setup"
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found"

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is not installed"
    echo "Please install FFmpeg with libplacebo support:"
    echo "  sudo apt install ffmpeg"
    exit 1
fi

echo "✅ FFmpeg found"

# Check libplacebo support
if ! ffmpeg -filters 2>&1 | grep -q libplacebo; then
    echo "⚠️  Warning: FFmpeg may not have libplacebo support"
    echo "You may need to compile FFmpeg with libplacebo"
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create directories
echo "📁 Creating directories..."
mkdir -p uploads outputs shaders

# Check shaders
shader_count=$(ls -1 shaders/*.glsl 2>/dev/null | wc -l)
echo "🎨 Found $shader_count Anime4K shaders"

if [ "$shader_count" -eq 0 ]; then
    echo "⚠️  No shaders found. They should have been downloaded during project creation."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Then open: http://localhost:5000"
