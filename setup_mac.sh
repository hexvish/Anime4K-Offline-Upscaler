#!/bin/bash
set -e

echo "🎬 Anime4K-Offline-Upscaler - macOS Setup"
echo "==========================================="

# Check Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install it from https://brew.sh"
    exit 1
fi
echo "✅ Homebrew found"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python 3..."
    brew install python
fi
echo "✅ Python 3 found"

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "📦 Installing FFmpeg..."
    brew install ffmpeg
fi
echo "✅ FFmpeg found"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate and install
source venv/bin/activate
echo "📦 Upgrading pip..."
pip install --upgrade pip
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create directories
echo "📁 Creating directories..."
mkdir -p uploads outputs shaders

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  ./launch_desktop.sh"
echo ""
