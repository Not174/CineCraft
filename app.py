import os
import subprocess
import json
import re
import webview

class CineCraftAPI:
    def __init__(self):
        self.window = None
        self.active_processes = {} # Track active tools

    def set_window(self, window):
        self.window = window

    def _run_ffmpeg(self, command, tool_prefix=None, progress_callback=None, duration=None, output_paths=None):
        """Runs ffmpeg command and reports progress if duration is provided."""
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        process = subprocess.Popen(
            command,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            creationflags=flags
        )

        if tool_prefix:
            # Store process and potential output files for cleanup
            paths = [output_paths] if isinstance(output_paths, str) else (output_paths or [])
            self.active_processes[tool_prefix] = {
                "process": process,
                "output_paths": paths
            }

        time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")

        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            if duration and progress_callback:
                match = time_regex.search(line)
                if match:
                    hours, minutes, seconds = match.groups()
                    current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    percent = min((current_time / duration) * 100, 99.9) # Max at 99.9 while processing
                    progress_callback(percent)

        ret = process.returncode
        
        # Cleanup tracker
        if tool_prefix in self.active_processes:
            del self.active_processes[tool_prefix]

        if ret == 0 and progress_callback:
            progress_callback(100) # Final 100% update

        return ret

    def cancel_task(self, prefix):
        """Signals a running process to terminate and cleans up partial files."""
        data = self.active_processes.get(prefix)
        if data:
            process = data.get("process")
            paths = data.get("output_paths", [])
            
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    process.terminate()
                
                # Cleanup partial files
                for p in paths:
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except:
                            pass # File might already be gone or locked

                return {"status": "success", "message": "Cancelled"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error", "message": "No active process"}

    def get_video_info(self, file_path):
        """Returns duration and stream information using ffprobe."""
        command = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path
        ]
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            result = subprocess.run(command, capture_output=True, text=True, creationflags=flags)
            return json.loads(result.stdout)
        except Exception:
            return None

    def choose_file(self):
        """JS bridge to open file dialog."""
        return self.open_file_dialog("Select File", allow_multiple=False)

    def choose_multiple(self):
        """JS bridge to open multiple files."""
        return self.open_file_dialog("Select Multiple Files", allow_multiple=True)

    def choose_save_path(self, extension=""):
        """JS bridge to open save dialog."""
        file_types = [f"Video (*{extension})"] if extension else ["All files (*.*)"]
        return self.save_file_dialog("Save File As", file_types)

    def convert_format(self, input_path, output_path, mode="transcode"):
        """Converts video format using either remuxing or transcoding."""
        info = self.get_video_info(input_path)
        duration = float(info['format']['duration']) if info else None
        
        if mode == "remux":
            # Fast Copy (Remuxing)
            command = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path]
        else:
            # Transcoding command (H.264 + AAC + Compatible Subtitles)
            is_mp4 = output_path.lower().endswith(".mp4")
            sub_codec = "mov_text" if is_mp4 else "copy"
            command = [
                "ffmpeg", "-y", "-i", input_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac",
                "-c:s", sub_codec,
                output_path
            ]
        
        def report_progress(p):
            if self.window:
                self.window.evaluate_js(f"updateProgress('conv', {p})")

        ret = self._run_ffmpeg(command, "conv", report_progress, duration, output_path)
        return {"status": "success" if ret == 0 else ("cancelled" if ret == -1 else "error"), 
                "message": "Done" if ret == 0 else ("Operation Cancelled" if ret != 0 else "Failed")}

    def merge_files(self, videos, audio=None, subtitle=None, output_path=None):
        """Merges videos, audio, and subtitles."""
        if not videos: return {"status": "error", "message": "No input"}
        
        total_dur = 0
        for v in videos:
            info = self.get_video_info(v)
            if info: total_dur += float(info.get('format', {}).get('duration', 0))

        # Simple merging for now (already optimized in previous turns)
        cmd = ["ffmpeg", "-y"]
        if len(videos) > 1:
            concat_path = os.path.join(os.path.dirname(output_path), "concat.txt")
            with open(concat_path, "w") as f:
                for v in videos: f.write(f"file '{v.replace('\\','/')}'\n")
            cmd += ["-f", "concat", "-safe", "0", "-i", concat_path]
        else:
            cmd += ["-i", videos[0]]

        if audio: cmd += ["-i", audio]
        if subtitle: cmd += ["-i", subtitle]
        
        cmd += ["-map", "0:v", "-map", "0:a?"]
        if audio: cmd += ["-map", "1:a"]
        if subtitle: cmd += ["-map", f"{2 if audio else 1}:s"]
        
        sub_codec = "mov_text" if output_path.lower().endswith(".mp4") else "copy"
        cmd += ["-c:v", "copy", "-c:a", "aac" if audio else "copy", "-c:s", sub_codec, output_path]

        def report_progress(p):
            if self.window:
                self.window.evaluate_js(f"updateProgress('merge', {p})")

        ret = self._run_ffmpeg(cmd, "merge", report_progress, total_dur, output_path)
        if len(videos) > 1 and os.path.exists(concat_path): os.remove(concat_path)
        return {"status": "success" if ret == 0 else "error", "message": "Done" if ret == 0 else "Failed or Cancelled"}

    def extract_streams(self, file_path, extract_type, output_dir=None):
        """Unified extraction of all tracks of a type (audio/subtitle)."""
        info = self.get_video_info(file_path)
        if not info: return {"status": "error", "message": "Failed to read file info"}

        def report_progress(p):
            if self.window:
                self.window.evaluate_js(f"updateProgress('extract', {p})")

        report_progress(10)
        
        streams = [s for s in info.get('streams', []) if s.get('codec_type') == extract_type]
        if not streams:
            return {"status": "error", "message": f"No {extract_type} streams found"}

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        target_dir = output_dir if output_dir else os.path.dirname(file_path)
        ext = "mp3" if extract_type == "audio" else "srt"
        
        # Build one big command to extract everything in one pass
        cmd = ["ffmpeg", "-y", "-i", file_path]
        out_paths = []
        for i, s in enumerate(streams):
            idx = s.get('index')
            out_file = os.path.join(target_dir, f"{base_name}_{extract_type}_{i}.{ext}")
            out_paths.append(out_file)
            cmd += ["-map", f"0:{idx}"]
            if extract_type == "audio":
                cmd += ["-c:a", "libmp3lame" if ext == "mp3" else "copy"]
            cmd += [out_file]

        report_progress(30)
        ret = self._run_ffmpeg(cmd, "extract", report_progress, None, out_paths)
        
        if ret == 0:
            report_progress(100)
            return {"status": "success", "message": f"Extracted {len(streams)} tracks successfully"}
        else:
            return {"status": "error", "message": "Extraction process failed or cancelled"}

    def crop_video(self, input_path, start, end, output_path, is_delete=False):
        """Crops or deletes a segment."""
        if not is_delete:
            cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", input_path, "-c", "copy", output_path]
            duration = end - start
        else:
            # Complex delete logic
            cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", f"select='not(between(t,{start},{end}))',setpts=N/FRAME_RATE/TB", "-af", f"aselect='not(between(t,{start},{end}))',asetpts=N/SR/TB", output_path]
            info = self.get_video_info(input_path)
            duration = float(info['format']['duration']) if info else None

        def report_progress(p):
            if self.window:
                self.window.evaluate_js(f"updateProgress('crop', {p})")

        ret = self._run_ffmpeg(cmd, "crop", report_progress, duration, output_path)
        return {"status": "success" if ret == 0 else "error", "message": "Done" if ret == 0 else "Failed or Cancelled"}

    def choose_folder(self):
        """JS bridge to open folder dialog."""
        return self.open_folder_dialog("Select Destination Folder")

    def open_file_dialog(self, title, allow_multiple=False, file_types=None):
        if not self.window: return None
        if not file_types: file_types = ("All files (*.*)",)
        res = self.window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=allow_multiple, file_types=file_types)
        if res and not allow_multiple: return res[0]
        return res

    def open_folder_dialog(self, title):
        if not self.window: return None
        res = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        return res[0] if res else None

    def save_file_dialog(self, title, file_types=None):
        if not self.window: return None
        if not file_types: file_types = ("All files (*.*)",)
        res = self.window.create_file_dialog(webview.SAVE_DIALOG, allow_multiple=False, file_types=file_types)
        return res[0] if res else None
