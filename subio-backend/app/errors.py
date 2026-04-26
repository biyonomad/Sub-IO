from fastapi import HTTPException
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
        self.code = code
        self.message = message


def file_too_large(limit_mb: int) -> AppError:
    return AppError(413, "FILE_TOO_LARGE", f"Upload exceeds {limit_mb} MB")


def unsupported_format(allowed: list[str]) -> AppError:
    return AppError(400, "UNSUPPORTED_FORMAT", f"Allowed formats: {', '.join(allowed)}")


def video_too_long(limit_minutes: int) -> AppError:
    return AppError(400, "VIDEO_TOO_LONG", f"Video exceeds {limit_minutes} minutes")


def audio_too_long(limit_minutes: int) -> AppError:
    return AppError(400, "AUDIO_TOO_LONG", f"Audio exceeds {limit_minutes} minutes")


def upload_not_found() -> AppError:
    return AppError(404, "UPLOAD_NOT_FOUND", "Upload not found")


def invalid_language() -> AppError:
    return AppError(400, "INVALID_LANGUAGE", "Unsupported language code")


def invalid_preset() -> AppError:
    return AppError(400, "INVALID_PRESET", "Unknown preset id")


def job_not_found() -> AppError:
    return AppError(404, "JOB_NOT_FOUND", "Job not found")


def file_not_found() -> AppError:
    return AppError(404, "FILE_NOT_FOUND", "File not found")


def internal_error() -> AppError:
    return AppError(500, "INTERNAL_ERROR", "Internal server error")


def translation_disabled() -> AppError:
    return AppError(400, "TRANSLATION_DISABLED", "Translation is disabled on this server")


def target_language_required() -> AppError:
    return AppError(400, "TARGET_LANGUAGE_REQUIRED", "target_language is required when translate=true")


def invalid_target_language() -> AppError:
    return AppError(400, "INVALID_TARGET_LANGUAGE", "Unsupported target language")


def openai_api_key_missing() -> AppError:
    return AppError(400, "OPENAI_API_KEY_MISSING", "OPENAI_API_KEY is not configured")


def error_response(exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        body = {"error": detail}
    else:
        body = {"error": {"code": "HTTP_ERROR", "message": str(detail)}}
    return JSONResponse(status_code=exc.status_code, content=body)
