import subprocess
from pathlib import Path


class FFmpegError(Exception):
    pass


def probe_duration(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError as exc:
        raise FFmpegError("ffprobe binary not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError("ffprobe timed out") from exc

    if result.returncode != 0:
        raise FFmpegError(f"ffprobe failed: {result.stderr.strip()[-300:]}")

    out = result.stdout.strip()
    if not out:
        raise FFmpegError("ffprobe produced no output")
    try:
        return float(out)
    except ValueError as exc:
        raise FFmpegError(f"ffprobe returned non-numeric duration: {out!r}") from exc


def extract_audio(in_path: Path, out_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(in_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(out_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60 * 60)
    except FileNotFoundError as exc:
        raise FFmpegError("ffmpeg binary not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError("ffmpeg timed out") from exc

    if result.returncode != 0:
        raise FFmpegError(f"ffmpeg failed: {result.stderr.strip()[-300:]}")
    if not out_path.is_file() or out_path.stat().st_size == 0:
        raise FFmpegError("ffmpeg produced empty output")
