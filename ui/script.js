const FOLDER_ICON = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>`;

window.onload = function() {
    document.querySelectorAll('.browse-btn').forEach(btn => {
        btn.innerHTML = FOLDER_ICON;
    });
};

const toolCardSelectors = {
    'conv': '.card-orange',
    'merge': '.card-yellow',
    'extract': '.card-blue',
    'crop': '.card-grey'
};

const toolViewIds = {
    'conv': 'view-converter',
    'merge': 'view-merge',
    'extract': 'view-extract',
    'crop': 'view-crop'
};

function toggleCardBusy(prefix, isBusy) {
    const selector = toolCardSelectors[prefix];
    if (selector) {
        const card = document.querySelector(selector);
        if (card) {
            if (isBusy) card.classList.add('busy');
            else card.classList.remove('busy');
        }
    }
}

const originalButtons = {
    'conv': { text: 'Start Convertion', func: 'runConverter()' },
    'merge': { text: 'Merge & Save', func: 'runMerge()' },
    'extract': { text: 'Execute Extraction', func: 'runExtract()' },
    'crop': { text: 'Process Video', func: 'runCrop()' }
};

function resetTool(prefix) {
    // Clear all inputs and selects within this tool's view
    const viewId = toolViewIds[prefix] || `view-${prefix}`;
    const view = document.getElementById(viewId);
    if (view) {
        view.querySelectorAll('input').forEach(input => input.value = "");
        view.querySelectorAll('select').forEach(select => select.selectedIndex = 0);
    }
    
    // Reset status elements
    const lbl = document.getElementById(`label-${prefix}`);
    if (lbl) lbl.innerText = "Ready";
    
    const msg = document.getElementById(`msg-${prefix}`);
    if (msg) {
        msg.innerText = "";
        msg.className = 'result-message';
    }
    
    const btn = document.querySelector(`#status-${prefix} .action-btn`);
    if (btn && originalButtons[prefix]) {
        btn.innerText = originalButtons[prefix].text;
        btn.classList.remove('btn-danger');
        btn.setAttribute('onclick', originalButtons[prefix].func);
    }

    toggleCardBusy(prefix, false);
    updateProgress(prefix, 0);
}

function navigate(viewId) {
    // Instant redirect: hide all views, show the target one
    document.querySelectorAll('.app-view').forEach(v => v.classList.add('hidden'));
    
    // Allow 'dashboard' or full view IDs like 'view-converter'
    const target = viewId === 'dashboard' ? 'view-dashboard' : 'view-' + viewId;
    const viewElem = document.getElementById(target);
    if (viewElem) viewElem.classList.remove('hidden');
}

function suggestPath(inputId, formatId) {
    const mainInput = document.getElementById(inputId).value;
    const formatElem = document.getElementById(formatId);
    if (!mainInput || !formatElem) return;
    
    const firstFile = mainInput.split('; ')[0];
    const format = formatElem.value;
    const dotIndex = firstFile.lastIndexOf('.');
    
    let path = firstFile;
    if (dotIndex !== -1) {
        path = firstFile.substring(0, dotIndex) + "_output" + format;
    } else {
        path = firstFile + "_output" + format;
    }

    if (inputId === 'conv-input') document.getElementById('conv-output-path').value = path;
    if (inputId === 'merge-videos') document.getElementById('merge-output-path').value = path;
    if (inputId === 'crop-input') document.getElementById('crop-output-path').value = path;
}

async function browseFile(inputId, formatId = null) {
    const file = await pywebview.api.choose_file();
    if (file) {
        document.getElementById(inputId).value = file;
        if (formatId) suggestPath(inputId, formatId);
    }
}

async function browseMultiple(inputId, formatId = null) {
    const files = await pywebview.api.choose_multiple();
    if (files && files.length > 0) {
        document.getElementById(inputId).value = files.join('; ');
        if (formatId) suggestPath(inputId, formatId);
    }
}

async function browseSavePath(inputId, formatId = null) {
    let extension = "";
    if (formatId) {
        const formatElem = document.getElementById(formatId);
        if (formatElem) extension = formatElem.value;
    }
    const path = await pywebview.api.choose_save_path(extension);
    if (path) {
        document.getElementById(inputId).value = path;
    }
}

// Progress Handlers (Per-tool)
function updateProgress(prefix, percent) {
    const bar = document.getElementById(`bar-${prefix}`);
    if (bar) bar.style.width = percent + '%';
    const pct = document.getElementById(`pct-${prefix}`);
    if (pct) pct.innerText = Math.round(percent) + '%';
}

function showProgress(prefix, statusText) {
    const msgArea = document.getElementById(`msg-${prefix}`);
    const lblArea = document.getElementById(`label-${prefix}`);
    const btn = document.querySelector(`#status-${prefix} .action-btn`);
    
    if (lblArea) lblArea.innerText = statusText;
    if (msgArea) {
        msgArea.innerText = "";
        msgArea.className = 'result-message';
    }

    if (btn) {
        btn.innerText = "Cancel";
        btn.classList.add('btn-danger');
        btn.setAttribute('onclick', `cancelTask('${prefix}')`);
    }

    toggleCardBusy(prefix, true);
    updateProgress(prefix, 0);
}

function showResult(prefix, message, isError = false) {
    const msgArea = document.getElementById(`msg-${prefix}`);
    const lblArea = document.getElementById(`label-${prefix}`);
    const btn = document.querySelector(`#status-${prefix} .action-btn`);
    
    if (lblArea) lblArea.innerText = isError ? "Error" : "Done";
    msgArea.innerText = message;
    msgArea.className = 'result-message ' + (isError ? 'error' : 'success');

    if (btn && originalButtons[prefix]) {
        btn.innerText = originalButtons[prefix].text;
        btn.classList.remove('btn-danger');
        btn.setAttribute('onclick', originalButtons[prefix].func);
    }

    toggleCardBusy(prefix, false);
}

async function cancelTask(prefix) {
    await pywebview.api.cancel_task(prefix);
}

// Runners
async function runConverter() {
    const inputPath = document.getElementById('conv-input').value;
    const savePath = document.getElementById('conv-output-path').value;
    const mode = document.getElementById('conv-mode').value;
    if (!inputPath || !savePath) return showResult('conv', 'Select input and output files.', true);

    showProgress('conv', 'Processing...');
    const res = await pywebview.api.convert_format(inputPath, savePath, mode);
    showResult('conv', res.message, res.status === 'error');
}

async function runMerge() {
    const vidsString = document.getElementById('merge-videos').value;
    const audio = document.getElementById('merge-audio').value;
    const sub = document.getElementById('merge-sub').value;
    const savePath = document.getElementById('merge-output-path').value;

    if (!vidsString || !savePath) return showResult('merge', 'Check inputs and output path.', true);
    const videos = vidsString.split('; ');

    showProgress('merge', 'Combining files...');
    const res = await pywebview.api.merge_files(videos, audio, sub, savePath);
    showResult('merge', res.message, res.status === 'error');
}

async function browseFolder(inputId) {
    const path = await pywebview.api.choose_folder();
    if (path) {
        document.getElementById(inputId).value = path;
    }
}

async function runExtract() {
    const inputPath = document.getElementById('extract-input').value;
    const type = document.getElementById('extract-type').value;
    const outputDir = document.getElementById('extract-output').value;
    if (!inputPath) return showResult('extract', 'Select a video file.', true);

    showProgress('extract', `Extracting ${type}s...`);
    const res = await pywebview.api.extract_streams(inputPath, type, outputDir || null);
    showResult('extract', res.message, res.status === 'error');
}

async function runCrop() {
    const inputPath = document.getElementById('crop-input').value;
    const start = parseFloat(document.getElementById('crop-start').value);
    const end = parseFloat(document.getElementById('crop-end').value);
    const mode = document.getElementById('crop-mode').value;
    const savePath = document.getElementById('crop-output-path').value;

    if (!inputPath || isNaN(start) || isNaN(end) || !savePath) return showResult('crop', 'Check all parameters.', true);

    showProgress('crop', 'Processing video...');
    const res = await pywebview.api.crop_video(inputPath, start, end, savePath, mode === 'delete');
    updateProgress('crop', 100);
    showResult('crop', res.message, res.status === 'error');
}
