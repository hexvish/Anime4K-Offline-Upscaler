"""
FFmpeg Manager - Auto-download and manage FFmpeg binaries
Automatically downloads the correct FFmpeg build for the user's platform on first run
"""
import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path
import json
import threading


class FFmpegManager:
    """Manages FFmpeg installation and provides path to executable"""

    # Download URLs for each platform
    DOWNLOAD_URLS = {
        'windows': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip',
            'executable': 'ffmpeg.exe',
            'probe': 'ffprobe.exe'
        },
        'linux': {
            # Use static build (gpl) instead of shared to avoid missing libraries
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz',
            'executable': 'ffmpeg',
            'probe': 'ffprobe'
        },
        'darwin': {  # macOS
            # Using evermeet.cx as BtbN doesn't provide macOS builds
            'url': 'https://evermeet.cx/ffmpeg/getrelease/zip',
            'executable': 'ffmpeg',
            'probe': 'ffprobe',
            'probe_url': 'https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip'
        }
    }

    def __init__(self, cache_dir=None):
        """
        Initialize FFmpeg Manager

        Args:
            cache_dir: Custom cache directory. If None, uses ./bin/<platform>/ in project directory
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Use project's bin directory instead of user home
            # This keeps FFmpeg local to the project
            project_root = Path(__file__).parent
            self.platform = self._detect_platform()
            self.cache_dir = project_root / 'bin' / self.platform

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if not hasattr(self, 'platform'):
            self.platform = self._detect_platform()
        self.download_progress = 0
        self.download_status = 'idle'  # idle, downloading, extracting, ready, error
        self.error_message = None

    def _detect_platform(self):
        """Detect the current platform"""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            return 'linux'
        elif system == 'darwin':
            return 'darwin'
        else:
            raise Exception(f"Unsupported platform: {system}")

    def get_ffmpeg_path(self):
        """Get path to FFmpeg executable, download if not exists"""
        config = self.DOWNLOAD_URLS[self.platform]
        ffmpeg_path = self.cache_dir / config['executable']

        if ffmpeg_path.exists():
            return str(ffmpeg_path)

        # FFmpeg not found, need to download
        return None

    def get_ffprobe_path(self):
        """Get path to FFprobe executable"""
        config = self.DOWNLOAD_URLS[self.platform]
        ffprobe_path = self.cache_dir / config['probe']

        if ffprobe_path.exists():
            return str(ffprobe_path)
        return None

    def is_installed(self):
        """Check if FFmpeg is already installed"""
        return self.get_ffmpeg_path() is not None

    def download_and_install(self, progress_callback=None):
        """
        Download and install FFmpeg for the current platform

        Args:
            progress_callback: Optional callback function(progress, status, message)
        """
        try:
            self.download_status = 'downloading'
            self.download_progress = 0

            config = self.DOWNLOAD_URLS[self.platform]
            download_url = config['url']

            # Determine file extension
            if download_url.endswith('.zip'):
                archive_path = self.cache_dir / 'ffmpeg_download.zip'
            elif download_url.endswith('.tar.xz'):
                archive_path = self.cache_dir / 'ffmpeg_download.tar.xz'
            else:
                archive_path = self.cache_dir / 'ffmpeg_download'

            # Download with progress
            def download_progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    downloaded = block_num * block_size
                    progress = min(100, int((downloaded / total_size) * 100))
                    self.download_progress = progress
                    if progress_callback:
                        progress_callback(
                            progress, 'downloading', f'Downloading FFmpeg: {progress}%')

            if progress_callback:
                progress_callback(0, 'downloading', 'Starting download...')

            urllib.request.urlretrieve(
                download_url, archive_path, download_progress_hook)

            # Extract
            self.download_status = 'extracting'
            if progress_callback:
                progress_callback(100, 'extracting', 'Extracting files...')

            self._extract_archive(archive_path)

            # Cleanup
            if archive_path.exists():
                archive_path.unlink()

            # For macOS, download ffprobe separately if needed
            if self.platform == 'darwin' and 'probe_url' in config:
                ffprobe_path = self.cache_dir / config['probe']
                if not ffprobe_path.exists():
                    probe_archive = self.cache_dir / 'ffprobe_download.zip'
                    urllib.request.urlretrieve(
                        config['probe_url'], probe_archive)
                    self._extract_archive(probe_archive)
                    if probe_archive.exists():
                        probe_archive.unlink()

            # Make executables executable on Unix systems
            if self.platform in ['linux', 'darwin']:
                ffmpeg_path = self.cache_dir / config['executable']
                ffprobe_path = self.cache_dir / config['probe']
                if ffmpeg_path.exists():
                    ffmpeg_path.chmod(0o755)
                if ffprobe_path.exists():
                    ffprobe_path.chmod(0o755)

            self.download_status = 'ready'
            self.download_progress = 100

            if progress_callback:
                progress_callback(100, 'ready', 'FFmpeg ready!')

            return True

        except Exception as e:
            self.download_status = 'error'
            self.error_message = str(e)
            if progress_callback:
                progress_callback(0, 'error', f'Error: {str(e)}')
            raise

    def _extract_archive(self, archive_path):
        """Extract downloaded archive"""
        if str(archive_path).endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Extract to temp directory first
                temp_dir = self.cache_dir / 'temp_extract'
                temp_dir.mkdir(exist_ok=True)
                zip_ref.extractall(temp_dir)

                # Find the bin directory and move executables
                self._move_executables_from_temp(temp_dir)

                # Cleanup temp
                shutil.rmtree(temp_dir)

        elif str(archive_path).endswith('.tar.xz'):
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                temp_dir = self.cache_dir / 'temp_extract'
                temp_dir.mkdir(exist_ok=True)
                tar_ref.extractall(temp_dir)

                self._move_executables_from_temp(temp_dir)
                shutil.rmtree(temp_dir)

    def _move_executables_from_temp(self, temp_dir):
        """Move executables from temp extraction directory to cache"""
        config = self.DOWNLOAD_URLS[self.platform]

        # Search for executables in temp directory
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file == config['executable'] or file == config.get('probe'):
                    src = Path(root) / file
                    dst = self.cache_dir / file
                    shutil.copy2(src, dst)
                # Also copy DLL files on Windows
                elif self.platform == 'windows' and file.endswith('.dll'):
                    src = Path(root) / file
                    dst = self.cache_dir / file
                    shutil.copy2(src, dst)

    def download_async(self, progress_callback=None, completion_callback=None):
        """Download FFmpeg in a background thread"""
        def download_thread():
            try:
                self.download_and_install(progress_callback)
                if completion_callback:
                    completion_callback(True, None)
            except Exception as e:
                if completion_callback:
                    completion_callback(False, str(e))

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
        return thread

    def get_status(self):
        """Get current download status"""
        return {
            'status': self.download_status,
            'progress': self.download_progress,
            'error': self.error_message,
            'installed': self.is_installed()
        }


# Global instance
_ffmpeg_manager = None


def get_ffmpeg_manager(cache_dir=None):
    """Get or create global FFmpeg manager instance"""
    global _ffmpeg_manager
    if _ffmpeg_manager is None:
        _ffmpeg_manager = FFmpegManager(cache_dir)
    return _ffmpeg_manager
