from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv
import threading
import uuid
import webview
import sys
import shutil
import zipfile
from datetime import datetime

# Linux specific fixes for Qt6/PySide6 segmentation faults
if sys.platform == "linux":
    if not os.environ.get('QT_QPA_PLATFORM'):
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'
    os.environ['QTWEBENGINE_CHROME_FLAGS'] = '--no-sandbox --disable-gpu-sandbox --enable-webgl --ignore-gpu-blocklist'

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['OUTPUT_FOLDER'] = os.getenv('OUTPUT_FOLDER', 'outputs')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE', 2147483648))
app.config['ALLOWED_EXTENSIONS'] = set(os.getenv('ALLOWED_EXTENSIONS', 'mp4,mkv,avi,mov,webm').split(','))

# Job storage (in-memory)
jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_video_info(filepath):
    """Get video duration and resolution using ffprobe"""
    try:
        if not filepath or not os.path.exists(filepath):
            return {'width': 0, 'height': 0, 'duration': 0, 'frames': 0}
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,nb_frames',
            '-show_entries', 'format=duration',
            '-of', 'json',
            filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        if not data.get('streams'): return {'width': 0, 'height': 0, 'duration': 0, 'frames': 0}
        stream = data['streams'][0]
        format_data = data.get('format', {})
        
        return {
            'width': stream.get('width', 0),
            'height': stream.get('height', 0),
            'duration': float(format_data.get('duration', 0)),
            'frames': int(stream.get('nb_frames', 0))
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {'width': 0, 'height': 0, 'duration': 0, 'frames': 0}

def calculate_resolution(video_info, mode, scale, custom_width, custom_height):
    """Calculate target resolution based on mode"""
    if mode == "Custom Resolution":
        try:
            w = int(custom_width) if custom_width else 1920
            h = int(custom_height) if custom_height else 1080
            # Ensure even numbers
            w = w if w % 2 == 0 else w + 1
            h = h if h % 2 == 0 else h + 1
            return max(2, w), max(2, h)
        except:
            return 1920, 1080
    else:
        base_w = video_info.get('width', 0) or 1920
        base_h = video_info.get('height', 0) or 1080
        width = int(base_w * scale)
        height = int(base_h * scale)
        # Ensure even numbers
        width = width if width % 2 == 0 else width + 1
        height = height if height % 2 == 0 else height + 1
        return max(2, width), max(2, height)

def process_batch(job_id, files_info, shader, quality, mode, scale, custom_w, custom_h):
    """Process multiple videos and bundle into a ZIP"""
    jobs[job_id]['status'] = 'processing'
    jobs[job_id]['start_time'] = time.time()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    processed_paths = []
    
    total_files = len(files_info)
    
    for i, file_info in enumerate(files_info):
        input_filename = file_info['name']
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        
        # Original name preservation
        output_filename = input_filename
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Resolution
        vid_info = get_video_info(input_path)
        width, height = calculate_resolution(vid_info, mode, scale, custom_w, custom_h)
        
        shader_path = os.path.join('shaders', shader)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', f'libplacebo=w={width}:h={height}:custom_shader_path={shader_path}',
            '-c:v', 'libx264',
            '-crf', str(quality),
            '-preset', 'medium',
            '-c:a', 'copy',
            '-progress', 'pipe:1',
            output_path
        ]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
            jobs[job_id]['active_process'] = process
            
            total_frames = vid_info.get('frames', 0)
            for line in process.stdout:
                if line.startswith('frame=') and total_frames > 0:
                    match = re.search(r'frame=\s*(\d+)', line)
                    if match:
                        current_frame = int(match.group(1))
                        # Progress is (current_file_index + file_progress) / total_files
                        file_progress = current_frame / total_frames
                        jobs[job_id]['progress'] = int(((i + file_progress) / total_files) * 100)
            
            process.wait()
            if process.returncode == 0:
                processed_paths.append(output_path)
            
        except Exception as e:
            print(f"Error processing {input_filename}: {e}")
            continue

    if not processed_paths:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = 'No files were successfully upscaled'
        return

    # Success logic
    jobs[job_id]['end_time'] = time.time()
    if total_files == 1:
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['output_file'] = os.path.basename(processed_paths[0])
    else:
        # ZIP multiple files
        zip_name = f"upscaled_collection_{timestamp}.zip"
        zip_path = os.path.join(app.config['OUTPUT_FOLDER'], zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in processed_paths:
                z.write(p, os.path.basename(p))
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['output_file'] = zip_name

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shaders')
def list_shaders():
    shader_dir = 'shaders'
    shaders = []
    if os.path.exists(shader_dir):
        for file in sorted(os.listdir(shader_dir)):
            if file.endswith('.glsl'):
                shaders.append({
                    'name': file,
                    'display_name': file.replace('Anime4K_', '').replace('.glsl', '').replace('_', ' ')
                })
    return jsonify(shaders)

@app.route('/gpu-info')
def gpu_info():
    """Get GPU information via FFmpeg"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-init_hw_device', 'vulkan', '-f', 'lavfi', '-i', 'nullsrc', '-t', '0.1', '-f', 'null', '-'],
            capture_output=True, text=True
        )
        gpus = [line.strip() for line in result.stderr.split('\n') if 'Device' in line or 'GPU' in line]
        return jsonify({'available': len(gpus) > 0, 'devices': gpus if gpus else ['CPU only']})
    except:
        return jsonify({'available': False, 'error': 'Detection failed'})

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    uploaded_files = request.files.getlist('files')
    results = []
    
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            info = get_video_info(filepath)
            results.append({
                'filename': filename,
                'size': os.path.getsize(filepath),
                'info': info
            })
    
    return jsonify(results)

@app.route('/process', methods=['POST'])
def start_processing():
    data = request.json
    filenames = data.get('filenames', []) # List of filenames
    shader = data.get('shader')
    mode = data.get('mode', 'Auto Scale')
    scale = float(data.get('scale', 2.0))
    custom_w = data.get('width', 3840)
    custom_h = data.get('height', 2160)
    quality = int(data.get('quality', 18))
    
    if not filenames:
        return jsonify({'error': 'No files to process'}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'id': job_id,
        'status': 'queued',
        'progress': 0,
        'output_file': None,
        'created_at': time.time()
    }
    
    files_info = [{'name': name} for name in filenames]
    
    thread = threading.Thread(
        target=process_batch,
        args=(job_id, files_info, shader, quality, mode, scale, custom_w, custom_h)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def job_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    # Create a copy to avoid removing data from the original dict
    job_copy = jobs[job_id].copy()
    job_copy.pop('active_process', None)
    
    # Calculate elapsed time
    if job_copy['status'] == 'processing':
        job_copy['elapsed'] = round(time.time() - job_copy.get('start_time', job_copy['created_at']), 1)
    elif job_copy.get('end_time'):
        job_copy['elapsed'] = round(job_copy['end_time'] - job_copy.get('start_time', job_copy['created_at']), 1)
    else:
        job_copy['elapsed'] = 0
        
    return jsonify(job_copy)

@app.route('/jobs')
def list_jobs():
    """List all jobs for the list view if needed"""
    job_list = []
    for job_id, job in jobs.items():
        job_copy = job.copy()
        job_copy.pop('active_process', None)
        job_list.append(job_copy)
    return jsonify(sorted(job_list, key=lambda x: x['created_at'], reverse=True))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/save-as/<filename>')
def save_as_proxy(filename):
    """Proxy for webview save dialog"""
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        active_window = webview.active_window()
        if not active_window: return jsonify({'error': 'Window not found'})
        
        file_types = ('Video files (*.mp4;*.mkv;*.avi;*.mov;*.webm)', 'Zip files (*.zip)', 'All files (*.*)')
        save_path = active_window.create_file_dialog(webview.FileDialog.SAVE, save_filename=filename, file_types=file_types)
        
        if save_path:
            if isinstance(save_path, (list, tuple)): save_path = save_path[0]
            shutil.copy2(file_path, save_path)
            return jsonify({'message': f'Saved to {save_path}'})
        return jsonify({'message': 'Save cancelled'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    job = jobs[job_id]
    if job.get('active_process'):
        job['active_process'].terminate()
        job['status'] = 'cancelled'
        return jsonify({'message': 'Job cancelled'})
    return jsonify({'error': 'Job not running'}), 400

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    PORT = 5000
    # Run Flask in a separate thread without debug mode to avoid signal issues
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    webview.create_window('Anime4K Premium Upscaler', f'http://127.0.0.1:{PORT}', width=1200, height=900)
    try:
        webview.start()
    except Exception as e:
        print(f"Webview failed: {e}")
        # Keep process alive so they can still use the browser
        while True:
            time.sleep(1)
    os._exit(0)
