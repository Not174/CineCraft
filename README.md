# CineCraft

A desktop video processing application built with Python, FastAPI, and pywebview. Fast, local, and private video operations without cloud uploads.

## Features

- **Convert**: Transform media between common delivery formats (MP4, MKV, WebM, etc.)
- **Merge**: Combine multiple clips with optional external audio and subtitles
- **Extract**: Pull audio or subtitle tracks into reusable files
- **Edit**: Trim or cut ranges from clips with live preview capabilities
- **Smart Proxies**: Generate browser-friendly preview files for heavy codecs

## Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3.13+, FastAPI, uvicorn
- **Desktop Integration**: pywebview (native file dialogs)
- **Media Engine**: FFmpeg / FFprobe
- **Build Tool**: PyInstaller

## System Requirements

- **Python**: 3.10 or higher (3.13+ recommended)
- **FFmpeg**: Latest version installed and in system PATH
- **OS**: Windows 10+ (optimized for Windows, Linux/Mac compatible)
- **RAM**: 4GB minimum for HD video, 8GB+ for 4K
- **Disk Space**: 2GB for application + space for video files

## Quick Start

### From Source

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd CineCraft
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg** (if not already installed)
   - **Windows**: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

5. **Run the application**
   ```bash
   python main.pyw
   ```

### Downloaded Executable

Simply run `CineCraft.exe` - no installation needed (except FFmpeg).

## Development

### Project Structure

```
CineCraft/
├── main.pyw              # Desktop app launcher
├── app.py                # FastAPI backend
├── requirements.txt      # Python dependencies
├── CineCraft.spec        # PyInstaller config
├── LICENSE               # MIT License
├── README.md            # This file
├── .gitignore           # Git ignore rules
├── ui/                  # Frontend (HTML/CSS/JS)
│   ├── index.html       # Main template
│   ├── script.js        # JavaScript logic
│   ├── style.css        # Styling & theme
│   └── assets/          # Images, icons
└── dist/                # Built executables (auto-generated)
```

### Build Executable

```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Build with PyInstaller
pyinstaller CineCraft.spec --clean
```

Output: `dist/CineCraft/CineCraft.exe`

## Running Modes

### Desktop Mode (Recommended)
```bash
python main.pyw
```
- Full native file dialogs
- System integration
- Best user experience

### Browser-First Dev Mode
```bash
python app.py
```
- Open `http://localhost:8000` in browser
- File dialogs unavailable (type paths manually)
- Useful for frontend development

## Troubleshooting

### FFmpeg not found
```
Error: FFmpeg is not installed or not in PATH
```
**Solution**: Install FFmpeg and add to system PATH. Verify with:
```bash
ffmpeg -version
```

### File dialogs not working
- Ensure you're running the desktop version (`main.pyw`)
- Browser-only mode doesn't support native dialogs

### Build fails
```bash
# Clean and rebuild
rm -r build/ dist/
pyinstaller CineCraft.spec --clean
```

## Configuration

Adjust in `main.pyw`:
- Window size: Default 1200x760 (minimum 1150x850)
- Background: Dark theme (#08090d)
- Server port: Auto-assigned random available port

## Features in Detail

### Supported Formats

**Video**: WebM, MP4, MKV, TS, MOV, AVI  
**Audio**: MP3, M4A, AAC  
**Subtitles**: SRT, ASS, VTT  

### Workflow Examples

**1. Convert to MP4 for Distribution**
- Select source → Choose format → Configure quality → Export

**2. Merge Clips with Audio**
- Add video clips → Layer audio track → Add subtitles → Merge

**3. Extract Subtitle Track**
- Load video → Select Extract → Choose SRT output → Save

**4. Quick Trim**
- Load video → Set trim range → Preview → Export trimmed version

## Performance Tips

- Use MP4 for maximum compatibility and reasonable quality
- MKV workflows use copy-based operations (faster, no re-encoding)
- Preview proxies are cached in `.runtime/` for faster repeated playback
- Local processing keeps your videos private (no cloud uploads)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [pywebview](https://pywebview.kivy.org/) - Lightweight Python web view
- [FFmpeg](https://ffmpeg.org/) - Media processing engine
- [PyInstaller](https://pyinstaller.org/) - Python to executable

## Support

For bugs, feature requests, or questions:
- Create an [Issue](../../issues) on GitHub
- Include steps to reproduce for bug reports
- Describe desired behavior for feature requests

## Roadmap

Future features:
- [ ] Video effects and filters
- [ ] Batch processing
- [ ] Custom encoding presets
- [ ] Cross-platform builds (macOS, Linux)
- [ ] Plugin support

---

**Made with ❤️ for video creators and editors
