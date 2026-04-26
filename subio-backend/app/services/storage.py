import os
import re
import secrets
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.settings import settings


_BASE = Path(settings.STORAGE_DIR).resolve()
UPLOADS_DIR = _BASE / "uploads"
AUDIO_DIR = _BASE / "audio"
OUTPUTS_DIR = _BASE / "outputs"


def ensure_dirs() -> None:
    for d in (_BASE, UPLOADS_DIR, AUDIO_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


ensure_dirs()


def new_id() -> str:
    return secrets.token_urlsafe(16)


_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    base = os.path.basename(name or "")
    base = base.replace("\x00", "")
    cleaned = _FILENAME_RE.sub("_", base).strip("._-")
    if not cleaned:
        cleaned = "file"
    if len(cleaned) > 80:
        root, dot, ext = cleaned.rpartition(".")
        if dot and len(ext) <= 8:
            cleaned = root[: 80 - len(ext) - 1] + "." + ext
        else:
            cleaned = cleaned[:80]
    return cleaned


def extension_of(name: str) -> str:
    return os.path.splitext(name)[1].lower().lstrip(".")


@dataclass
class FileEntry:
    path: Path
    filename: str
    mime: str
    kind: str  # "txt" | "srt"


class FileRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, FileEntry] = {}
        self._lock = threading.RLock()

    def register(self, file_id: str, entry: FileEntry) -> None:
        with self._lock:
            self._entries[file_id] = entry

    def get(self, file_id: str) -> Optional[FileEntry]:
        with self._lock:
            return self._entries.get(file_id)


file_registry = FileRegistry()


@dataclass
class UploadEntry:
    path: Path
    original_filename: str
    sanitized_filename: str
    size_bytes: int
    duration_seconds: float


class UploadRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, UploadEntry] = {}
        self._lock = threading.RLock()

    def register(self, upload_id: str, entry: UploadEntry) -> None:
        with self._lock:
            self._entries[upload_id] = entry

    def get(self, upload_id: str) -> Optional[UploadEntry]:
        with self._lock:
            return self._entries.get(upload_id)


upload_registry = UploadRegistry()


def safe_remove(path: Path) -> None:
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass
