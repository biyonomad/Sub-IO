from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse

from app import errors
from app.services import storage

router = APIRouter()

_ALLOWED_KINDS = {"txt", "srt"}


def _lookup(file_id: str) -> storage.FileEntry:
    entry = storage.file_registry.get(file_id)
    if entry is None or entry.kind not in _ALLOWED_KINDS:
        raise errors.file_not_found()
    if not entry.path.is_file():
        raise errors.file_not_found()
    return entry


@router.get("/api/preview/{file_id}")
def preview(file_id: str) -> PlainTextResponse:
    entry = _lookup(file_id)
    text = entry.path.read_text(encoding="utf-8")
    return PlainTextResponse(content=text, media_type="text/plain; charset=utf-8")


@router.get("/api/download/{file_id}")
def download(file_id: str) -> FileResponse:
    entry = _lookup(file_id)
    return FileResponse(
        path=entry.path,
        media_type=entry.mime,
        filename=entry.filename,
    )
