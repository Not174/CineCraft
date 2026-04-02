# Changelog

All notable changes to CineCraft will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- [ ] Batch processing improvements
- [ ] Custom preset saving
- [ ] Advanced color grading tools
- [ ] Hardware acceleration (GPU support)
- [ ] Plugin system
- [ ] Keyboard shortcuts customization
- [ ] Dark/Light theme switcher
- [ ] Integration with external APIs

---

## [1.0.0] - 2024-12-XX

### Added
- Initial release of CineCraft
- **Core Features:**
  - Video conversion between multiple formats (MP4, WebM, MKV, MOV, AVI)
  - Batch conversion support with multiple file handling
  - Video merge/concatenation with timeline preview
  - Audio extraction from videos
  - Video editing capabilities (trim, crop, scale, rotate)
  - Metadata editing
  - FFmpeg integration with progress tracking
  - Real-time processing statistics

- **UI/UX:**
  - Dark-themed desktop interface
  - Native file dialogs for system integration
  - Responsive layout with tool navigation
  - Status indicators and error messages
  - Custom dark title bar with window controls
  - Asset gallery with visual previews

- **Backend:**
  - FastAPI-based REST API
  - Async processing with uvicorn
  - Python-based FFmpeg wrapper
  - Automatic port assignment for server
  - Thread-safe operations

- **Developer Features:**
  - PyInstaller-ready Windows executable build
  - Comprehensive README documentation
  - Contributing guidelines
  - MIT License
  - .gitignore for Python projects
  - Modern Python 3.13 support

### Technical Stack
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Backend:** Python 3.13, FastAPI, uvicorn
- **Desktop:** pywebview 5.4+
- **Build:** PyInstaller 6.19.0
- **Media:** FFmpeg/FFprobe

### Fixed
- API initialization timing in JavaScript (waitForAPI function)
- Window control buttons (minimize, maximize, close) in executable
- File dialog functionality in bundled .exe
- Error handling for failed operations

### Documentation
- Complete README with installation and usage guides
- Troubleshooting section for common issues
- Project structure documentation
- Build instructions for creating executables
- Contributing guidelines for developers

---

## Version History Notes

### v1.0.0 Development Timeline

**Phase 1: Core Development**
- Built FastAPI backend with FFmpeg integration
- Created dark-themed HTML/CSS/JS frontend
- Implemented file dialogs and API bridge

**Phase 2: Desktop Integration**
- Integrated pywebview for native window
- Created custom dark title bar
- Implemented window controls

**Phase 3: Build & Distribution**
- Configured PyInstaller for Windows .exe creation
- Fixed API timing issues in bundled application
- Optimized build settings (console=False, windowed=True, onedir mode)

**Phase 4: Documentation & Release**
- Created comprehensive README
- Added MIT License
- Configured .gitignore
- Prepared for GitHub publication

---

## Upgrading

### From Pre-Release to v1.0.0
No previous versions - this is the initial release.

---

## Known Limitations (v1.0.0)

- **Windows Only:** Currently builds for Windows; Mac/Linux support planned
- **Single File Limits:** Very large files (>5GB) may need more testing
- **FFmpeg Dependency:** Users must install FFmpeg separately
- **Real-time Preview:** Some operations don't show live preview
- **Hardware Acceleration:** Currently uses CPU only; GPU support planned

---

## Roadmap

### v1.1.0 (Planned)
- [ ] User preferences/settings dialog
- [ ] Recent files history
- [ ] Drag-and-drop file support
- [ ] Improved progress indicators
- [ ] Copy processing parameters

### v1.2.0 (Planned)
- [ ] Mac support
- [ ] Linux support
- [ ] Keyboard shortcuts
- [ ] Undo/Redo functionality
- [ ] Template system for common conversions

### v2.0.0 (Planned)
- [ ] Hardware acceleration (GPU)
- [ ] Plugin system
- [ ] Advanced color grading
- [ ] Timeline editor
- [ ] Cloud sync for presets

---

## Migration Guides

*None available yet - this is v1.0.0*

---

## Support & Feedback

- **Report Bugs:** GitHub Issues
- **Suggest Features:** GitHub Discussions
- **Contribute Code:** GitHub Pull Requests
- **General Questions:** GitHub Discussions

---

## Credits

This project was created with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [pywebview](https://pywebview.kivy.org/) - Desktop GUI wrapper
- [FFmpeg](https://ffmpeg.org/) - Media processing engine
- [PyInstaller](https://pyinstaller.org/) - Executable builder

---

## License

CineCraft is released under the MIT License. See [LICENSE](LICENSE) file for details.

---

**Latest Update:** Initial Release (v1.0.0)  
**Next Scheduled Release:** 2025-Q2 (v1.1.0)

