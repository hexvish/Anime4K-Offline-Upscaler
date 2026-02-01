// State
let selectedFiles = [];
let shaders = [];
let activeJobId = null;
let pollInterval = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileListArea = document.getElementById('file-list-area');
const fileList = document.getElementById('file-list');
const shaderSelect = document.getElementById('shader-select');
const qualityInput = document.getElementById('quality-input');
const qualityValue = document.getElementById('quality-value');
const resModeRadios = document.querySelectorAll('input[name="res-mode"]');
const autoResRow = document.getElementById('auto-res-row');
const customResRow = document.getElementById('custom-res-row');
const scaleInput = document.getElementById('scale-input');
const widthInput = document.getElementById('width-input');
const heightInput = document.getElementById('height-input');
const processBtn = document.getElementById('process-btn');
const consoleStatus = document.getElementById('console-status');
const resultArea = document.getElementById('result-area');
const successMsg = document.getElementById('success-msg');
const saveBtn = document.getElementById('save-btn');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const gpuStatus = document.getElementById('gpu-status');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadShaders();
    setupEventListeners();
    checkGPU();
});

function setupEventListeners() {
    // Dropzone
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

    // Quality slider
    qualityInput.addEventListener('input', (e) => { qualityValue.textContent = e.target.value; });

    // Res Mode Toggle
    resModeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const isAuto = e.target.value === 'Auto Scale';
            autoResRow.style.display = isAuto ? 'grid' : 'none';
            customResRow.style.display = isAuto ? 'none' : 'grid';
        });
    });

    // Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // Process
    processBtn.addEventListener('click', startUpscaling);

    // Save As
    saveBtn.addEventListener('click', handleSaveAs);
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    handleFiles(e.dataTransfer.files);
}

function handleFiles(files) {
    if (files.length === 0) return;

    selectedFiles = Array.from(files);
    fileList.innerHTML = '';

    selectedFiles.forEach(file => {
        const li = document.createElement('li');
        li.className = 'file-item';
        li.innerHTML = `<span>${file.name}</span> <span>${(file.size / (1024 * 1024)).toFixed(2)} MB</span>`;
        fileList.appendChild(li);
    });

    fileListArea.style.display = 'block';
}

async function loadShaders() {
    try {
        const response = await fetch('/shaders');
        shaders = await response.json();
        shaderSelect.innerHTML = shaders.map(s => `<option value="${s.name}">${s.display_name}</option>`).join('');
    } catch (e) {
        shaderSelect.innerHTML = '<option>Error loading shaders</option>';
    }
}

async function checkGPU() {
    try {
        const resp = await fetch('/gpu-info');
        const data = await resp.json();
        gpuStatus.textContent = data.available ? `✅ GPU: ${data.devices[0]}` : "⚠️ GPU: CPU Only (Vulkan not detected)";
    } catch (e) {
        gpuStatus.textContent = "❌ GPU: Detection failed";
    }
}

async function startUpscaling() {
    if (selectedFiles.length === 0) {
        alert("Please select at least one file.");
        return;
    }

    // Reset Console
    consoleStatus.innerHTML = '<p class="waiting-msg">⏳ Initializing...</p>';
    resultArea.style.display = 'none';
    processBtn.disabled = true;

    try {
        // 1. Upload files first
        consoleStatus.innerHTML = '<p class="waiting-msg">📤 Uploading files...</p>';
        const formData = new FormData();
        selectedFiles.forEach(f => formData.append('files', f));

        const uploadResp = await fetch('/upload', { method: 'POST', body: formData });
        const uploadedFiles = await uploadResp.json();

        // 2. Start processing
        consoleStatus.innerHTML = '<p class="waiting-msg">🚀 Starting engine...</p>';
        const processData = {
            filenames: uploadedFiles.map(f => f.filename),
            shader: shaderSelect.value,
            mode: document.querySelector('input[name="res-mode"]:checked').value,
            scale: parseFloat(scaleInput.value),
            width: parseInt(widthInput.value),
            height: parseInt(heightInput.value),
            quality: parseInt(qualityInput.value)
        };

        const procResp = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(processData)
        });
        const job = await procResp.json();
        activeJobId = job.job_id;

        // 3. Start Polling
        startPolling();

    } catch (e) {
        consoleStatus.innerHTML = `<p class="error-msg">❌ Error: ${e.message}</p>`;
        processBtn.disabled = false;
    }
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(async () => {
        if (!activeJobId) return;

        try {
            const resp = await fetch(`/status/${activeJobId}`);
            if (resp.status === 404) {
                clearInterval(pollInterval);
                activeJobId = null;
                processBtn.disabled = false;
                consoleStatus.innerHTML = '<p class="waiting-msg">Job state lost. Please try again.</p>';
                return;
            }
            const job = await resp.json();

            updateConsole(job);

            if (job.status === 'completed') {
                clearInterval(pollInterval);
                finishJob(job);
            } else if (job.status === 'failed') {
                clearInterval(pollInterval);
                failJob(job);
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 1000);
}

function updateConsole(job) {
    const progress = job.progress || 0;
    const elapsed = job.elapsed || 0;
    consoleStatus.innerHTML = `
        <div class="progress-card">
            <div class="area-header">Status: ${job.status.toUpperCase()}</div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: ${progress}%"></div>
            </div>
            <div class="progress-meta">
                <span>Overall Progress: ${progress}%</span>
                <span>⏱️ ${elapsed}s</span>
            </div>
        </div>
    `;
}

function finishJob(job) {
    activeJobId = null;
    processBtn.disabled = false;
    const elapsed = job.elapsed || 0;
    successMsg.innerHTML = `<strong>✅ Success!</strong> ${job.output_file} <span class="time-stamp">(Time: ${elapsed}s)</span>`;
    resultArea.style.display = 'block';
    saveBtn.dataset.filename = job.output_file;
}

function failJob(job) {
    activeJobId = null;
    processBtn.disabled = false;
    consoleStatus.innerHTML = `<p style="color: var(--error)">❌ Failed: ${job.error || 'Unknown error'}</p>`;
}

async function handleSaveAs() {
    const filename = saveBtn.dataset.filename;
    if (!filename) return;

    saveBtn.disabled = true;
    saveBtn.textContent = '💾 Pending...';

    try {
        const resp = await fetch(`/save-as/${filename}`);
        const data = await resp.json();
        if (data.message) {
            console.log(data.message);
        }
    } catch (e) {
        alert("Save failed: " + e.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save As...';
    }
}
