# CineCraft

A powerful, premium-looking video processing toolkit for Windows.

## Features

- **Format Converter**: Seamlessly convert between MKV, MP4, and TS formats.
- **Merge**: Combine multiple videos, audios, and subtitles into a single file. Optimized for fast MKV merging with optional MP4 conversion.
- **Extract**: Extract all audio and subtitle tracks from any video file.
- **Crop & Delete**: Clip specific segments or remove unwanted portions from your videos.

## Requirements

- Python 3.10+
- FFmpeg (Must be in your system PATH)

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Creating an Executable

To bundle CineCraft into a single `.exe` file for distribution:
```bash
pyinstaller --onefile --windowed --add-data "ui;ui" --add-data "staff.ico;." --icon="staff.ico" main.py
```

## UI Design
CineCraft features a modern, glassmorphic UI with vibrant colors and smooth animations, inspired by professional editing software.

![CineCraft Dashboard](ui/assets/staff.png)
