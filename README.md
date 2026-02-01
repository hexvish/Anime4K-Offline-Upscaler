# Anime4K-Offline-Upscaler

A standalone premium offline application for GPU-accelerated video upscaling using Anime4K GLSL shaders and FFmpeg libplacebo.

## Features

- 🌐 **Modern Web Interface** - Drag-and-drop video uploads
- 🎨 **Anime4K Shaders** - 38+ high-quality upscaling shaders
- 🚀 **GPU Accelerated** - Uses system GPU via Vulkan/libplacebo
- 📊 **Real-time Progress** - Monitor upscaling jobs live
- 💾 **Batch Processing** - Queue multiple videos
- 🎯 **Quality Control** - Adjustable CRF and resolution settings
- 📱 **Responsive Design** - Works on desktop and mobile

## System Requirements

- **OS**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.11+
- **FFmpeg**: With libplacebo support
- **GPU**: Vulkan-compatible (NVIDIA/AMD)
- **RAM**: 4GB+ recommended
- **Disk**: Sufficient space for uploads and outputs

## Installation & Launch

### 🐧 Linux

#### 1. Setup
```bash
git clone https://github.com/hexvish/Anime4K-Offline-Upscaler.git
cd Anime4K-Offline-Upscaler
chmod +x setup.sh launch_desktop.sh
./setup.sh
```

#### 2. Launch
- **Desktop Mode**: `./launch_desktop.sh`
- **Server Mode**: `source venv/bin/activate && python app.py`

---

### 🪟 Windows

#### 1. Setup
- Ensure [Python 3.11+](https://www.python.org/downloads/windows/) and [FFmpeg](https://ffmpeg.org/download.html#build-windows) are installed and in your PATH.
- Double-click **`setup.bat`**.

#### 2. Launch
- Double-click **`launch_desktop.bat`**.

---

## Usage

### Basic Workflow

1. **Upload Video**
   - Drag & drop or click to browse
   - Supported: MP4, MKV, AVI, MOV, WEBM
   - Max size: 2GB

2. **Configure Settings**
   - **Shader**: Choose quality preset
     - `Upscale Denoise CNN x2 M` - Balanced (recommended)
     - `Upscale Denoise CNN x2 L` - High quality
     - `Upscale Denoise CNN x2 S` - Fast/low VRAM
   - **Resolution**: Auto-set to 2x (customizable)
   - **Quality (CRF)**: 15-28 (18 recommended)

3. **Start Processing**
   - Click "Start Upscaling"
   - Monitor progress in real-time
   - Download when complete

### Shader Guide

**Recommended Shaders:**

| Shader | Quality | Speed | VRAM | Use Case |
|--------|---------|-------|------|----------|
| `Upscale_Denoise_CNN_x2_M` | ⭐⭐⭐ | ⭐⭐⭐ | Medium | General purpose |
| `Upscale_Denoise_CNN_x2_L` | ⭐⭐⭐⭐ | ⭐⭐ | High | Best quality |
| `Upscale_Denoise_CNN_x2_S` | ⭐⭐ | ⭐⭐⭐⭐ | Low | 4GB VRAM systems |
| `Upscale_CNN_x2_M` | ⭐⭐⭐ | ⭐⭐⭐⭐ | Low | No denoising |
| `Restore_CNN_M` | ⭐⭐⭐ | ⭐⭐⭐⭐ | Low | Restoration only |

### Quality Settings

**CRF (Constant Rate Factor):**
- **15-17**: Very high quality, large files
- **18-20**: High quality (recommended)
- **21-23**: Good quality, balanced size
- **24-28**: Lower quality, small files

## Technical Details

### FFmpeg Command

The app constructs commands like:

```bash
ffmpeg -i input.mp4 \
  -vf "libplacebo=w=1920:h=1080:custom_shader_path=shaders/Anime4K_Upscale_Denoise_CNN_x2_M.glsl" \
  -c:v libx264 -crf 18 -preset medium \
  -c:a copy \
  output.mp4
```

### GPU Acceleration

- Uses **Vulkan** via libplacebo filter
- Automatically detects available GPUs
- Falls back to CPU if Vulkan unavailable

### File Storage

```
anime4k-web/
├── uploads/     # Temporary uploaded videos
├── outputs/     # Processed videos
└── shaders/     # Anime4K GLSL shaders
```

## Troubleshooting

### "GPU: CPU Only" Warning

**Cause**: FFmpeg doesn't have Vulkan support

**Fix**:
```bash
# Check FFmpeg filters
ffmpeg -filters | grep libplacebo

# If missing, install FFmpeg with libplacebo:
sudo apt install ffmpeg
```

### Processing Fails Immediately

**Cause**: Invalid shader or FFmpeg error

**Fix**:
- Check FFmpeg installation
- Verify shader files exist in `shaders/`
- Check logs in terminal

### Out of Memory

**Cause**: Video too large or VRAM insufficient

**Fix**:
- Use smaller input videos
- Use "S" (small) shader variants
- Lower output resolution
- Close other GPU applications

### Slow Processing

**Cause**: CPU processing or high quality settings

**Fix**:
- Verify GPU is being used (check terminal output)
- Use faster shader presets
- Increase CRF value (lower quality)
- Use "medium" or "fast" preset

## API Endpoints

For programmatic access:

```
GET  /                    - Web interface
GET  /shaders             - List available shaders
GET  /gpu-info            - GPU detection info
POST /upload              - Upload video file
POST /process             - Start processing job
GET  /status/<job_id>     - Get job status
GET  /jobs                - List all jobs
GET  /download/<filename> - Download processed video
POST /cancel/<job_id>     - Cancel running job
```

## Configuration

Edit `.env` file:

```env
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
MAX_FILE_SIZE=2147483648  # 2GB
ALLOWED_EXTENSIONS=mp4,mkv,avi,mov,webm
DEFAULT_SHADER=Anime4K_Upscale_Denoise_CNN_x2_M.glsl
FFMPEG_THREADS=4
GPU_DEVICE=0
```

## Performance Tips

1. **Use appropriate shaders** for your GPU
2. **Process in batches** during off-hours
3. **Monitor GPU temperature** during heavy use
4. **Clean up old files** regularly
5. **Use SSD** for faster I/O

## Credits

- **Anime4K**: [bloc97/Anime4K](https://github.com/bloc97/Anime4K)
- **FFmpeg**: [ffmpeg.org](https://ffmpeg.org)
- **libplacebo**: [haasn/libplacebo](https://github.com/haasn/libplacebo)

## License

This web application is provided as-is. Anime4K shaders are licensed under MIT. FFmpeg is licensed under LGPL/GPL.

## Support

For issues:
1. Check terminal logs
2. Verify FFmpeg libplacebo support
3. Test with small video files first
4. Check GPU compatibility

---

**Made with ❤️ for the anime community**
