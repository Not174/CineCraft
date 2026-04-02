# CineCraft Development Guide

Complete guide for setting up the development environment and understanding the codebase architecture.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Architecture](#project-architecture)
3. [Code Organization](#code-organization)
4. [API Reference](#api-reference)
5. [Development Workflow](#development-workflow)
6. [Debugging Guide](#debugging-guide)
7. [Performance Optimization](#performance-optimization)
8. [Common Issues](#common-issues)

---

## Development Setup

### Prerequisites

- **Python 3.10+** (Tested with 3.13)
- **Git** for version control
- **FFmpeg** installed and in system PATH
- **Node.js** (optional, for future web UI enhancements)

### Windows Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/CineCraft.git
cd CineCraft

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify FFmpeg installation
ffmpeg -version
ffprobe -version

# 6. Run application
python main.pyw
```

### Linux/Mac Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/CineCraft.git
cd CineCraft

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify FFmpeg installation
ffmpeg -version
ffprobe -version

# 6. Run application
python main.pyw
```

### Setting Up FFmpeg

**Windows:**
```bash
# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
# Add to PATH manually
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg      # CentOS/RHEL
```

---

## Project Architecture

### High-Level Overview

```
┌─────────────────────────────────────────┐
│   CineCraft Desktop Application         │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   Frontend (UI Layer)            │   │
│  │  ├─ index.html (Structure)       │   │
│  │  ├─ script.js (Logic)            │   │
│  │  └─ style.css (Appearance)       │   │
│  └──────────────────────────────────┘   │
│              ↕ pywebview API bridge      │
│  ┌──────────────────────────────────┐   │
│  │   Backend (Application Layer)    │   │
│  │  ├─ main.pyw (Entry point)       │   │
│  │  └─ app.py (FastAPI routes)      │   │
│  └──────────────────────────────────┘   │
│              ↕ subprocess calls          │
│  ┌──────────────────────────────────┐   │
│  │   Media Layer                    │   │
│  │  └─ FFmpeg/FFprobe               │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Data Flow

1. **User Action** (Frontend)
   - User clicks button or selects files
   - JavaScript event handler triggered

2. **API Request** (Frontend → Backend)
   - JavaScript calls `window.pywebview.api.method()`
   - Request sent to FastAPI backend

3. **Processing** (Backend)
   - FastAPI route receives request
   - Constructs FFmpeg command
   - Spawns subprocess for processing

4. **Media Processing** (FFmpeg)
   - FFmpeg executes video operations
   - Returns success/error status

5. **Response** (Backend → Frontend)
   - FastAPI returns result JSON
   - Frontend updates UI with status

---

## Code Organization

### Main Files

#### `main.pyw`
**Purpose:** Application entry point and window management

**Key Classes:**
```python
class ServerThread(Thread):
    """Runs FastAPI server in background thread"""
    - Starts uvicorn server
    - Finds available port
    - Manages server lifecycle

class DialogBridge:
    """Bridge between frontend file dialogs and pywebview API"""
    - choose_file() - Single file selection
    - choose_multiple() - Multiple file selection
    - choose_folder() - Directory selection
    - choose_save_path() - Save file dialog
```

**Key Functions:**
```python
if __name__ == '__main__':
    - Creates window
    - Starts server thread
    - Bridges API methods
    - Shows application
```

#### `app.py`
**Purpose:** FastAPI backend implementation

**Key Routes:**
```python
@app.post("/process/convert")
- Convert video between formats

@app.post("/process/merge")
- Merge/concatenate videos

@app.post("/process/extract")
- Extract audio from video

@app.post("/process/edit")
- Edit video (trim, crop, scale, rotate)

@app.post("/process/metadata")
- Edit video metadata
```

**Helper Functions:**
```python
def run_ffmpeg(command):
    - Execute FFmpeg subprocess
    - Handle errors and output

def get_video_info(filepath):
    - Extract video metadata using FFprobe
```

#### `ui/index.html`
**Purpose:** Frontend HTML structure

**Key Sections:**
```html
<div class="title-bar">
<!-- Custom window frame -->

<div class="app-shell">
    <div class="tool-selector">
    <!-- Navigation buttons -->
    
    <div class="tool-content">
    <!-- Content for each tool -->
```

#### `ui/script.js`
**Purpose:** Frontend logic and API communication

**Key Functions:**
```javascript
async function waitForAPI(timeout = 5000)
- Waits for pywebview API initialization

function bindBrowseButtons()
- Attaches file dialog handlers

async function handleBrowse(event)
- Opens file dialog and handles selection

async function runConversion()
async function runMerge()
async function runExtract()
async function runEdit()
- Tool-specific processing functions
```

#### `ui/style.css`
**Purpose:** All styling and theming

**Key Sections:**
```css
:root - CSS variables (colors, sizes)
.title-bar - Custom window frame
.tool-* - Tool-specific styles
.button, .input, .select - Form elements
@media queries - Responsive design
```

---

## API Reference

### Frontend → Backend API

All calls through `window.pywebview.api`:

#### File Dialogs
```javascript
// Single file selection
await window.pywebview.api.choose_file(
    title,
    allow_multiple=false,
    file_types=[]
)

// Multiple files
await window.pywebview.api.choose_multiple()

// Folder selection
await window.pywebview.api.choose_folder()

// Save dialog
await window.pywebview.api.choose_save_path()
```

### Backend → FFmpeg API

#### FastAPI Routes

```
POST /process/convert
Request: {
    "input_file": "path/to/input.mp4",
    "output_file": "path/to/output.webm",
    "codec": "vp9",
    "bitrate": "2M"
}
Response: {"status": "success", "message": "..."}

POST /process/merge
Request: {
    "files": ["file1.mp4", "file2.mp4"],
    "output_file": "merged.mp4"
}

POST /process/extract
Request: {
    "input_file": "video.mp4",
    "output_file": "audio.mp3"
}

POST /process/edit
Request: {
    "input_file": "video.mp4",
    "output_file": "edited.mp4",
    "trim": {"start": 10, "end": 60},
    "crop": {"x": 0, "y": 0, "w": 1920, "h": 1080},
    "scale": "1280:720",
    "rotate": 90
}
```

---

## Development Workflow

### Adding a New Feature

#### Example: Add Image Watermark Tool

**Step 1: Backend Route** (`app.py`)
```python
@app.post("/process/watermark")
async def process_watermark(request: dict):
    """Add watermark to video"""
    input_file = request.get("input_file")
    watermark_file = request.get("watermark_file")
    output_file = request.get("output_file")
    
    # FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-i", watermark_file,
        "-filter_complex", "[0:v][1:v] overlay=10:10",
        output_file
    ]
    
    return run_ffmpeg(cmd)
```

**Step 2: Frontend UI** (`ui/index.html`)
```html
<!-- Add button in tool selector -->
<button class="tool-link-card" data-route="watermark">
    Add Watermark
</button>

<!-- Add content panel -->
<div class="tool-content-panel" data-tool="watermark">
    <h2>Add Watermark to Video</h2>
    <div class="form-group">
        <label>Video File:</label>
        <input type="text" id="watermark-input" readonly>
        <button class="browse-btn" data-browse="watermark-input">Browse</button>
    </div>
    <div class="form-group">
        <label>Watermark Image:</label>
        <input type="text" id="watermark-img" readonly>
        <button class="browse-btn" data-browse="watermark-img">Browse</button>
    </div>
    <button class="action-btn" data-action="watermark">Add Watermark</button>
</div>
```

**Step 3: Frontend Logic** (`ui/script.js`)
```javascript
async function runWatermark() {
    const inputFile = document.getElementById('watermark-input').value;
    const watermarkImg = document.getElementById('watermark-img').value;
    
    const outputFile = await window.pywebview.api.choose_save_path();
    
    const response = await fetch('/process/watermark', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            input_file: inputFile,
            watermark_file: watermarkImg,
            output_file: outputFile
        })
    });
    
    const result = await response.json();
    alert(result.message);
}
```

**Step 4: Wire Event Handler** (`ui/script.js`)
```javascript
// In bindActionButtons()
if (button.dataset.action === 'watermark') {
    button.addEventListener('click', runWatermark);
}
```

---

## Debugging Guide

### Enabling Debug Logging

**In `main.pyw`:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Creating window...")
logger.debug(f"Server running on port {port}")
```

**In `app.py`:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.post("/process/convert")
async def process_convert(request: dict):
    logger.debug(f"Convert request: {request}")
    # ... processing
    logger.debug(f"Command: {' '.join(cmd)}")
```

### Browser DevTools

Open developer console in pywebview:

```python
# In main.pyw, enable dev tools
api = DialogBridge()
window = pywebview.create_window(
    'CineCraft',
    'http://localhost:' + str(port),
    js_api=api,
    background_color='#08090d',
    frameless=True,
    min_size=(1150, 850),
    webview_kwargs={'debug': True}  # Enable debug mode
)
```

### Common Debug Scenarios

**Issue: API not available**
```javascript
// Check API initialization
console.log(window.pywebview);
console.log(window.pywebview?.api);
```

**Issue: FFmpeg command fails**
```python
# Add stderr capture
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
stdout, stderr = process.communicate()
print(f"STDERR: {stderr}")
```

**Issue: Port already in use**
```python
# Use socket to find available port
import socket
with socket.socket() as s:
    s.bind(('', 0))
    port = s.getsockname()[1]
```

---

## Performance Optimization

### FFmpeg Optimization

```python
# Use hardware acceleration if available
cmd = [
    "ffmpeg",
    "-hwaccel", "cuda",  # or "qsv" for Intel, "videotoolbox" for Mac
    "-i", input_file,
    output_file
]

# Optimize encoding
cmd = [
    "ffmpeg",
    "-i", input_file,
    "-c:v", "libx265",  # H.265 for better compression
    "-crf", "28",        # Quality (0-51, lower=better)
    "-preset", "fast",   # Speed vs quality tradeoff
    output_file
]
```

### Frontend Performance

```css
/* Use GPU acceleration */
.app-shell {
    transform: translateZ(0);
    will-change: transform;
}

/* Optimize animations */
.transition-smooth {
    transition: all 0.3s ease-out;
}
```

### Memory Management

```python
# Process large files in chunks
def process_large_file(input_file, chunk_size=1024*1024):
    with open(input_file, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            # Process chunk
```

---

## Common Issues

### Issue: "FFmpeg not found"

**Solution:**
```bash
# Verify FFmpeg is in PATH
ffmpeg -version

# Add to PATH (Windows)
set PATH=%PATH%;C:\ffmpeg\bin

# Add to PATH (Linux/Mac)
export PATH=$PATH:/usr/local/bin
```

### Issue: "Port already in use"

**Solution:**
```python
# The app already handles this, but manual fix:
import socket
def get_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]
```

### Issue: "API not initializing in .exe"

**Solution:**
Already fixed in current version with `waitForAPI()` function.

```javascript
// Already implemented
async function waitForAPI(timeout = 5000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        if (window.pywebview && window.pywebview.api) return true;
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    return false;
}
```

### Issue: "Video file won't process"

**Solution:**
```bash
# Check file integrity
ffprobe input.mp4

# Try different codec
ffmpeg -i input.mp4 -c:v libx264 output.mp4

# Check FFmpeg version
ffmpeg -version
```

---

## Building for Distribution

### Create Executable

```bash
# Clean previous build
rmdir /s build dist

# Build using spec file
pyinstaller CineCraft.spec --clean

# Test executable
dist/CineCraft/CineCraft.exe
```

### PyInstaller Configuration

See `CineCraft.spec` for current settings:

```python
a = Analysis(
    ['main.pyw'],
    pathex=[],
    binaries=[],
    datas=[('ui', 'ui'), ('staff.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
```

---

## Version Control Best Practices

### Branch Naming
```
feature/feature-name
fix/bug-description
docs/documentation-update
refactor/code-organization
```

### Commit Messages
```
feat: Add watermark feature
fix: Resolve API timeout issue
docs: Update README with examples
refactor: Simplify FFmpeg command builder
```

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Changes tested locally
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pywebview Documentation](https://pywebview.kivy.org/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Python Subprocess](https://docs.python.org/3/library/subprocess.html)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/usage.html)

---

**For questions or issues, please open an issue on GitHub!**
