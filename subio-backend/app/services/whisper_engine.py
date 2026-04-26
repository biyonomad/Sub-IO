import threading
from pathlib import Path
from typing import Optional

from app.settings import settings


_model = None
_model_lock = threading.Lock()


def _resolve_device(requested: str) -> str:
    if requested and requested.lower() != "auto":
        return requested
    try:
        import torch
    except Exception:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_model():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        import whisper
        device = _resolve_device(settings.WHISPER_DEVICE)
        _model = whisper.load_model(settings.WHISPER_MODEL, device=device)
        return _model


def transcribe(audio_path: Path, language: Optional[str]) -> dict:
    model = get_model()
    kwargs = {"verbose": False}
    if language and language != "auto":
        kwargs["language"] = language
    result = model.transcribe(str(audio_path), **kwargs)
    segments = []
    for seg in result.get("segments", []) or []:
        segments.append({
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "text": (seg.get("text") or "").strip(),
        })
    return {
        "language": result.get("language") or language or "auto",
        "segments": segments,
        "text": (result.get("text") or "").strip(),
    }
