from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent
UI = ROOT / "ui"
RUNTIME = ROOT / ".runtime"
PREVIEWS = RUNTIME / "previews"
ARCHIVES = RUNTIME / "archives"
TEMP = RUNTIME / "temp"
TIME_RE = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d+)")
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def reset_runtime() -> None:
    if RUNTIME.exists():
        shutil.rmtree(RUNTIME, ignore_errors=True)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)


def fmt_seconds(value: float | int | None) -> str:
    if value is None:
        return "--:--"
    total = max(int(float(value)), 0)
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def fmt_bytes(value: float | int | str | None) -> str:
    if value in (None, ""):
        return "Unknown"
    size = float(value)
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    return f"{size:.1f} {units[index]}"


def probe_json(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=FLAGS,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("Unable to inspect media with ffprobe.")
    return json.loads(result.stdout)


def require_file(path_str: str, label: str) -> Path:
    path = Path(path_str).expanduser()
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=400, detail=f"{label} was not found.")
    return path


def require_output(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if not path.name:
        raise HTTPException(status_code=400, detail="Choose a valid output filename.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def maybe_dir(path_str: str | None, fallback: Path) -> Path:
    if not path_str:
        return fallback
    path = Path(path_str).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def browser_friendly(path: Path, info: dict) -> bool:
    ext = path.suffix.lower()
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), {})
    vcodec = video.get("codec_name", "").lower()
    acodec = audio.get("codec_name", "").lower()
    if ext == ".webm":
        return vcodec in {"vp8", "vp9", "av1"} and acodec in {"opus", "vorbis", ""}
    if ext in {".mp4", ".m4v", ".mov"}:
        return vcodec in {"h264", "av1", "mpeg4"} and acodec in {"aac", "mp3", "ac3", ""}
    return False


def subtitle_codec(output: Path) -> str:
    return "mov_text" if output.suffix.lower() == ".mp4" else "copy"


def extract_target(kind: str, codec: str, subtitle_format: str | None = None) -> tuple[str, list[str]]:
    if kind == "audio":
        return "mp3", ["-vn", "-c:a", "libmp3lame", "-q:a", "2"]
    if subtitle_format in {"srt", "ass"}:
        return subtitle_format, ["-c:s", subtitle_format]
    mapping = {
        "subrip": ("srt", ["-c:s", "copy"]),
        "ass": ("ass", ["-c:s", "copy"]),
        "ssa": ("ssa", ["-c:s", "copy"]),
        "webvtt": ("vtt", ["-c:s", "copy"]),
        "mov_text": ("srt", ["-c:s", "srt"]),
        "hdmv_pgs_subtitle": ("sup", ["-c:s", "copy"]),
        "dvd_subtitle": ("sub", ["-c:s", "copy"]),
    }
    return mapping.get(codec, ("srt", ["-c:s", "srt"]))


class Store:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.jobs: dict[str, dict] = {}
        self.media: dict[str, Path] = {}

    def create(self, kind: str, title: str, details: dict | None = None) -> dict:
        job = {
            "job_id": uuid4().hex[:10],
            "kind": kind,
            "title": title,
            "details": details or {},
            "status": "queued",
            "progress": 0.0,
            "message": "Queued",
            "created_at": time.time(),
            "updated_at": time.time(),
            "artifacts": [],
            "cleanup": [],
            "command": [],
            "logs": [],
            "process": None,
        }
        with self.lock:
            self.jobs[job["job_id"]] = job
        return job

    def get(self, job_id: str) -> dict:
        with self.lock:
            job = self.jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return job

    def update(self, job_id: str, **changes) -> None:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found.")
            job.update(changes)
            job["updated_at"] = time.time()

    def append_log(self, job_id: str, line: str) -> None:
        clean = line.strip()
        if not clean:
            return
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job["logs"].append(clean)
            job["logs"] = job["logs"][-8:]
            job["updated_at"] = time.time()

    def media_url(self, path: Path) -> str:
        token = uuid4().hex
        with self.lock:
            self.media[token] = path
        return f"/api/media/{token}"

    def media_path(self, token: str) -> Path:
        with self.lock:
            path = self.media.get(token)
        if not path or not path.exists():
            raise HTTPException(status_code=404, detail="Preview asset not found.")
        return path

    def recent(self, limit: int = 12) -> list[dict]:
        with self.lock:
            jobs = sorted(self.jobs.values(), key=lambda item: item["created_at"], reverse=True)
        return [self.serialize(job) for job in jobs[:limit]]

    def snapshot(self, job_id: str) -> dict:
        return self.serialize(self.get(job_id))

    def serialize(self, job: dict) -> dict:
        artifacts = []
        for index, artifact in enumerate(job["artifacts"]):
            url = self.media_url(artifact["path"]) if artifact["role"] == "media" else f"/api/jobs/{job['job_id']}/artifacts/{index}"
            artifacts.append(
                {
                    "label": artifact["label"],
                    "filename": artifact.get("download_name") or artifact["path"].name,
                    "url": url,
                    "role": artifact["role"],
                    "size_label": fmt_bytes(artifact["path"].stat().st_size if artifact["path"].exists() else None),
                }
            )
        return {
            "job_id": job["job_id"],
            "kind": job["kind"],
            "title": job["title"],
            "details": job["details"],
            "status": job["status"],
            "progress": round(job["progress"], 1),
            "message": job["message"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "artifacts": artifacts,
            "logs": job["logs"][-4:],
            "command_preview": " ".join(job["command"]),
        }

    def cancel(self, job_id: str) -> dict:
        job = self.get(job_id)
        self.update(job_id, status="cancelling", message="Cancelling...")
        process = job.get("process")
        if process and process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False, creationflags=FLAGS)
            else:
                process.terminate()
        for path in job.get("cleanup", []):
            try:
                if Path(path).exists() and Path(path).is_file():
                    Path(path).unlink()
            except OSError:
                pass
        self.update(job_id, status="cancelled", progress=100, message="Job cancelled.")
        return self.snapshot(job_id)


store = Store()


class ProbeRequest(BaseModel):
    path: str


class PreviewRequest(BaseModel):
    path: str


class ConvertRequest(BaseModel):
    input_path: str
    output_path: str
    mode: str = "remux"


class MergeRequest(BaseModel):
    videos: list[str] = Field(min_length=1)
    output_path: str
    audio: str | None = None
    subtitle: str | None = None


class ExtractRequest(BaseModel):
    input_path: str
    extract_type: str
    output_dir: str | None = None
    subtitle_format: str | None = None


class EditRequest(BaseModel):
    input_path: str
    output_path: str
    mode: str
    start: float
    end: float


def run_job(job: dict, target) -> None:
    def wrapper() -> None:
        store.update(job["job_id"], status="running", message="Processing...")
        try:
            target()
        except Exception as exc:
            store.update(job["job_id"], status="failed", progress=100, message=str(exc))

    threading.Thread(target=wrapper, daemon=True).start()


def run_ffmpeg(
    job_id: str,
    command: list[str],
    duration: float | None = None,
    start_progress: float = 0.0,
    end_progress: float = 99.0,
) -> int:
    current_progress = float(store.get(job_id).get("progress", 0.0) or 0.0)
    store.update(job_id, command=command, progress=max(current_progress, start_progress))
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=FLAGS,
    )
    store.update(job_id, process=process)
    try:
        while True:
            line = process.stderr.readline() if process.stderr else ""
            if not line and process.poll() is not None:
                break
            if not line:
                continue
            store.append_log(job_id, line)
            match = TIME_RE.search(line)
            if match and duration:
                hours, minutes, seconds = match.groups()
                elapsed = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                ratio = min(elapsed / max(duration, 0.001), 0.995)
                progress = start_progress + ratio * max(end_progress - start_progress, 0.0)
                store.update(job_id, progress=progress, message="Encoding in progress...")
    finally:
        code = process.wait()
        store.update(job_id, process=None)
    return -1 if store.get(job_id)["status"] == "cancelled" else code


def trim_command(source: Path, output: Path, start: float, end: float) -> list[str]:
    return [
        "ffmpeg", "-y", "-i", str(source), "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-c:s", subtitle_codec(output), "-movflags", "+faststart", str(output),
    ]


def cut_command(source: Path, output: Path, info: dict, start: float, end: float, duration: float) -> list[str]:
    has_audio = any(stream.get("codec_type") == "audio" for stream in info.get("streams", []))
    if start <= 0.01:
        return trim_command(source, output, end, duration)
    if end >= duration - 0.01:
        return trim_command(source, output, 0, start)
    if has_audio:
        filters = (
            f"[0:v]trim=0:{start:.3f},setpts=PTS-STARTPTS[v0];"
            f"[0:a]atrim=0:{start:.3f},asetpts=PTS-STARTPTS[a0];"
            f"[0:v]trim=start={end:.3f},setpts=PTS-STARTPTS[v1];"
            f"[0:a]atrim=start={end:.3f},asetpts=PTS-STARTPTS[a1];"
            "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
        )
        return [
            "ffmpeg", "-y", "-i", str(source), "-filter_complex", filters,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-movflags", "+faststart", str(output),
        ]
    filters = (
        f"[0:v]trim=0:{start:.3f},setpts=PTS-STARTPTS[v0];"
        f"[0:v]trim=start={end:.3f},setpts=PTS-STARTPTS[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[v]"
    )
    return [
        "ffmpeg", "-y", "-i", str(source), "-filter_complex", filters,
        "-map", "[v]", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-movflags", "+faststart", str(output),
    ]


def health() -> dict:
    return {
        "app": "CineCraft",
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "workspace": str(ROOT),
    }


def probe_payload(path_str: str) -> dict:
    source = require_file(path_str, "Source media")
    info = probe_json(source)
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    audio_tracks = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    subtitle_tracks = [s for s in info.get("streams", []) if s.get("codec_type") == "subtitle"]
    preview_needed = not browser_friendly(source, info)
    return {
        "path": str(source),
        "name": source.name,
        "duration": duration,
        "duration_label": fmt_seconds(duration),
        "size_label": fmt_bytes(info.get("format", {}).get("size")),
        "video_codec": video.get("codec_name", "unknown"),
        "audio_tracks": len(audio_tracks),
        "subtitle_tracks": len(subtitle_tracks),
        "preview_needed": preview_needed,
        "media_url": None if preview_needed else store.media_url(source),
        "streams": info.get("streams", []),
    }


def start_preview(path_str: str) -> dict:
    source = require_file(path_str, "Source media")
    info = probe_json(source)
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    preview = PREVIEWS / f"{uuid4().hex[:10]}_preview.mp4"
    job = store.create("preview", "Generating preview proxy", {"source": source.name})
    store.update(job["job_id"], cleanup=[preview])

    def worker() -> None:
        command = [
            "ffmpeg", "-y", "-i", str(source), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-vf", "scale=-2:720", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(preview),
        ]
        code = run_ffmpeg(job["job_id"], command, duration, start_progress=2, end_progress=99)
        if code == 0:
            store.update(job["job_id"], status="completed", progress=100, message="Preview is ready.", artifacts=[{"label": "Preview proxy", "path": preview, "role": "media"}])
        elif code == -1:
            store.update(job["job_id"], status="cancelled", progress=100, message="Preview cancelled.")
        else:
            store.update(job["job_id"], status="failed", progress=100, message="Preview generation failed.")

    run_job(job, worker)
    return store.snapshot(job["job_id"])


def start_convert(payload: ConvertRequest) -> dict:
    source = require_file(payload.input_path, "Source file")
    output = require_output(payload.output_path)
    duration = float(probe_json(source).get("format", {}).get("duration", 0) or 0)
    job = store.create("convert", "Format conversion", {"source": source.name, "output": output.name})
    store.update(job["job_id"], cleanup=[output])

    def worker() -> None:
        if payload.mode == "remux":
            command = [
                "ffmpeg", "-y", "-i", str(source),
                "-map", "0:v?", "-map", "0:a?", "-map", "0:s?",
                "-c", "copy",
                str(output),
            ]
        else:
            command = [
                "ffmpeg", "-y", "-i", str(source),
                "-map", "0:v?", "-map", "0:a?", "-map", "0:s?",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "aac", "-c:s", subtitle_codec(output), "-movflags", "+faststart", str(output),
            ]
        code = run_ffmpeg(job["job_id"], command, duration, start_progress=2, end_progress=99)
        if code == 0:
            store.update(job["job_id"], status="completed", progress=100, message="Conversion finished successfully.", artifacts=[{"label": "Download output", "path": output, "role": "download"}])
        elif code == -1:
            store.update(job["job_id"], status="cancelled", progress=100, message="Conversion cancelled.")
        else:
            store.update(job["job_id"], status="failed", progress=100, message="Conversion failed.")

    run_job(job, worker)
    return store.snapshot(job["job_id"])


def start_merge(payload: MergeRequest) -> dict:
    videos = [require_file(item, f"Video {index + 1}") for index, item in enumerate(payload.videos)]
    audio = require_file(payload.audio, "Audio file") if payload.audio else None
    subtitle = require_file(payload.subtitle, "Subtitle file") if payload.subtitle else None
    output = require_output(payload.output_path)
    duration = sum(float(probe_json(path).get("format", {}).get("duration", 0) or 0) for path in videos)
    job = store.create("merge", "Merge media", {"clips": len(videos), "output": output.name})
    concat = TEMP / f"{job['job_id']}_concat.txt"

    def worker() -> None:
        command = ["ffmpeg", "-y"]
        cleanup = [output]
        if len(videos) > 1:
            concat.write_text("".join(f"file '{str(path).replace(chr(92), '/')}'\n" for path in videos), encoding="utf-8")
            cleanup.append(concat)
            command += ["-f", "concat", "-safe", "0", "-i", str(concat)]
        else:
            command += ["-i", str(videos[0])]
        audio_index = None
        subtitle_index = None
        next_index = 1
        if audio:
            command += ["-i", str(audio)]
            audio_index = next_index
            next_index += 1
        if subtitle:
            command += ["-i", str(subtitle)]
            subtitle_index = next_index
        command += ["-map", "0:v:0", "-map", "0:a?"]
        if audio_index is not None:
            command += ["-map", f"{audio_index}:a:0"]
        if subtitle_index is not None:
            command += ["-map", f"{subtitle_index}:s:0"]
        if output.suffix.lower() == ".mp4":
            command += ["-c:v", "libx264", "-preset", "fast", "-crf", "21", "-c:a", "aac", "-c:s", "mov_text", "-movflags", "+faststart", str(output)]
        else:
            command += ["-c:v", "copy", "-c:a", "copy", "-c:s", "copy", str(output)]
        store.update(job["job_id"], cleanup=cleanup)
        code = run_ffmpeg(job["job_id"], command, duration, start_progress=2, end_progress=99)
        if concat.exists():
            try:
                concat.unlink()
            except OSError:
                pass
        if code == 0:
            store.update(job["job_id"], status="completed", progress=100, message="Merge complete.", artifacts=[{"label": "Download merged file", "path": output, "role": "download"}])
        elif code == -1:
            store.update(job["job_id"], status="cancelled", progress=100, message="Merge cancelled.")
        else:
            store.update(job["job_id"], status="failed", progress=100, message="Merge failed.")

    run_job(job, worker)
    return store.snapshot(job["job_id"])


def start_extract(payload: ExtractRequest) -> dict:
    source = require_file(payload.input_path, "Source file")
    info = probe_json(source)
    streams = [stream for stream in info.get("streams", []) if stream.get("codec_type") == payload.extract_type]
    if not streams:
        raise HTTPException(status_code=400, detail=f"No {payload.extract_type} streams were found.")
    subtitle_format = (payload.subtitle_format or "srt").lower() if payload.extract_type == "subtitle" else None
    if subtitle_format and subtitle_format not in {"srt", "ass"}:
        raise HTTPException(status_code=400, detail="Subtitle output format must be either SRT or ASS.")
    target = maybe_dir(payload.output_dir, source.parent)
    details = {"source": source.name, "tracks": len(streams)}
    if subtitle_format:
        details["format"] = subtitle_format
    job = store.create("extract", f"Extract {payload.extract_type}", details)

    def worker() -> None:
        cleanup = []
        artifacts = []
        total_streams = len(streams)
        for index, stream in enumerate(streams, start=1):
            ext, codec_args = extract_target(payload.extract_type, (stream.get("codec_name") or "track").lower(), subtitle_format)
            output = target / f"{source.stem}_{payload.extract_type}_{index}.{ext}"
            cleanup.append(output)
            store.update(job["job_id"], cleanup=cleanup)
            command = ["ffmpeg", "-y", "-i", str(source), "-map", f"0:{stream.get('index')}", *codec_args, str(output)]
            segment_start = ((index - 1) / total_streams) * 96
            segment_end = (index / total_streams) * 96
            store.update(job["job_id"], progress=segment_start, message=f"Extracting track {index} of {total_streams}.")
            code = run_ffmpeg(job["job_id"], command, None, start_progress=segment_start, end_progress=segment_end)
            if code == -1:
                store.update(job["job_id"], status="cancelled", progress=100, message="Extraction cancelled.")
                return
            if code != 0:
                store.update(job["job_id"], status="failed", progress=100, message="Extraction failed.")
                return
            artifacts.append({"label": f"Track {index}", "path": output, "role": "download"})
            store.update(job["job_id"], progress=segment_end, message=f"Extracted track {index} of {total_streams}.")
        if len(artifacts) > 1:
            archive = ARCHIVES / f"{job['job_id']}_extracts.zip"
            store.update(job["job_id"], progress=98, message="Packaging extracted tracks.")
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for artifact in artifacts:
                    bundle.write(artifact["path"], arcname=artifact["path"].name)
            artifacts.insert(0, {"label": "Download all as ZIP", "path": archive, "role": "download"})
        store.update(job["job_id"], status="completed", progress=100, message="Extraction complete.", artifacts=artifacts)

    run_job(job, worker)
    return store.snapshot(job["job_id"])


def start_edit(payload: EditRequest) -> dict:
    source = require_file(payload.input_path, "Source file")
    output = require_output(payload.output_path)
    info = probe_json(source)
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    if payload.end <= payload.start:
        raise HTTPException(status_code=400, detail="The end time must be greater than the start time.")
    if payload.start < 0 or payload.end > duration:
        raise HTTPException(status_code=400, detail="The selected range is outside the clip duration.")
    job = store.create("edit", "Edit clip", {"source": source.name, "output": output.name})
    store.update(job["job_id"], cleanup=[output])

    def worker() -> None:
        command = trim_command(source, output, payload.start, payload.end) if payload.mode == "trim" else cut_command(source, output, info, payload.start, payload.end, duration)
        target_duration = payload.end - payload.start if payload.mode == "trim" else duration
        code = run_ffmpeg(job["job_id"], command, target_duration, start_progress=2, end_progress=99)
        if code == 0:
            store.update(job["job_id"], status="completed", progress=100, message="Edit exported successfully.", artifacts=[{"label": "Download edited clip", "path": output, "role": "download"}])
        elif code == -1:
            store.update(job["job_id"], status="cancelled", progress=100, message="Editing cancelled.")
        else:
            store.update(job["job_id"], status="failed", progress=100, message="Editing failed.")

    run_job(job, worker)
    return store.snapshot(job["job_id"])


reset_runtime()
app = FastAPI(title="CineCraft", version="2.0.0")
app.mount("/static", StaticFiles(directory=str(UI)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(UI / "index.html")


for route in ("/convert", "/merge", "/extract", "/edit"):
    app.add_api_route(route, index, methods=["GET"], include_in_schema=False)


@app.get("/api/health")
def api_health() -> dict:
    return health()


@app.get("/api/jobs")
def api_jobs() -> dict:
    return {"items": store.recent()}


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str) -> dict:
    return store.snapshot(job_id)


@app.post("/api/jobs/{job_id}/cancel")
def api_cancel(job_id: str) -> dict:
    return store.cancel(job_id)


@app.get("/api/jobs/{job_id}/artifacts/{artifact_index}")
def api_artifact(job_id: str, artifact_index: int) -> FileResponse:
    job = store.get(job_id)
    if artifact_index < 0 or artifact_index >= len(job["artifacts"]):
        raise HTTPException(status_code=404, detail="Artifact not found.")
    artifact = job["artifacts"][artifact_index]
    if artifact["role"] != "download":
        raise HTTPException(status_code=400, detail="Artifact is not downloadable.")
    return FileResponse(artifact["path"], filename=artifact.get("download_name") or artifact["path"].name)


@app.get("/api/media/{token}")
def api_media(token: str) -> FileResponse:
    return FileResponse(store.media_path(token))


@app.post("/api/probe")
def api_probe(payload: ProbeRequest) -> dict:
    return probe_payload(payload.path)


@app.post("/api/previews")
def api_preview(payload: PreviewRequest) -> dict:
    return start_preview(payload.path)


@app.post("/api/jobs/convert")
def api_convert(payload: ConvertRequest) -> dict:
    return start_convert(payload)


@app.post("/api/jobs/merge")
def api_merge(payload: MergeRequest) -> dict:
    return start_merge(payload)


@app.post("/api/jobs/extract")
def api_extract(payload: ExtractRequest) -> dict:
    return start_extract(payload)


@app.post("/api/jobs/edit")
def api_edit(payload: EditRequest) -> dict:
    return start_edit(payload)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
