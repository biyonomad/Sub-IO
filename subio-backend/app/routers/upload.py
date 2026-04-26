import logging

from fastapi import APIRouter, File, Header, UploadFile

from app import errors
from app.schemas import UploadResponse
from app.services import storage
from app.services.ffmpeg import probe_duration, FFmpegError
from app.settings import settings

router = APIRouter()
logger = logging.getLogger("subio.upload")

ALLOWED_EXTS = {"mp4", "mov", "m4v", "mkv", "avi"}
CHUNK_SIZE = 1024 * 1024


@router.post("/api/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    content_length: int | None = Header(default=None),
) -> UploadResponse:
    raw_name = file.filename or ""
    sanitized = storage.sanitize_filename(raw_name)
    ext = storage.extension_of(sanitized)
    if ext not in ALLOWED_EXTS:
        raise errors.unsupported_format(sorted(ALLOWED_EXTS))

    max_bytes = settings.max_upload_size_bytes
    if content_length is not None and content_length > max_bytes:
        raise errors.file_too_large(settings.MAX_UPLOAD_SIZE_MB)

    upload_id = storage.new_id()
    dest = storage.UPLOADS_DIR / f"{upload_id}.{ext}"

    total = 0
    try:
        with dest.open("wb") as out:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    out.close()
                    storage.safe_remove(dest)
                    raise errors.file_too_large(settings.MAX_UPLOAD_SIZE_MB)
                out.write(chunk)
    except errors.AppError:
        raise
    except Exception:
        logger.exception("Failed to write upload")
        storage.safe_remove(dest)
        raise errors.internal_error()
    finally:
        await file.close()

    if total == 0:
        storage.safe_remove(dest)
        raise errors.unsupported_format(sorted(ALLOWED_EXTS))

    try:
        duration = probe_duration(dest)
    except FFmpegError:
        logger.exception("ffprobe failed for upload %s", upload_id)
        storage.safe_remove(dest)
        raise errors.unsupported_format(sorted(ALLOWED_EXTS))

    if duration > settings.max_video_duration_seconds:
        storage.safe_remove(dest)
        raise errors.video_too_long(settings.MAX_VIDEO_DURATION_MINUTES)

    storage.upload_registry.register(
        upload_id,
        storage.UploadEntry(
            path=dest,
            original_filename=raw_name,
            sanitized_filename=sanitized,
            size_bytes=total,
            duration_seconds=duration,
        ),
    )

    return UploadResponse(
        upload_id=upload_id,
        filename=sanitized,
        size_bytes=total,
        duration_seconds=round(duration, 3),
    )
