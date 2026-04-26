from fastapi import APIRouter, BackgroundTasks

from app import errors
from app.languages import SUPPORTED_LANGUAGE_CODES, SUPPORTED_TARGET_LANGUAGE_CODES
from app.presets import PRESETS_BY_ID
from app.schemas import TranscribeRequest, TranscribeResponse
from app.services import storage
from app.services.job_store import Job, job_store
from app.services.pipeline import run_transcription
from app.settings import settings

router = APIRouter()


@router.post("/api/transcribe", response_model=TranscribeResponse)
def transcribe(req: TranscribeRequest, background_tasks: BackgroundTasks) -> TranscribeResponse:
    if req.language not in SUPPORTED_LANGUAGE_CODES:
        raise errors.invalid_language()
    if req.preset_id not in PRESETS_BY_ID:
        raise errors.invalid_preset()
    if storage.upload_registry.get(req.upload_id) is None:
        raise errors.upload_not_found()

    if req.translate:
        if not settings.ENABLE_TRANSLATION:
            raise errors.translation_disabled()
        if not req.target_language:
            raise errors.target_language_required()
        if req.target_language not in SUPPORTED_TARGET_LANGUAGE_CODES:
            raise errors.invalid_target_language()
        if not settings.OPENAI_API_KEY:
            raise errors.openai_api_key_missing()

    job_id = storage.new_id()
    job = Job(
        id=job_id,
        upload_id=req.upload_id,
        language=req.language,
        preset_id=req.preset_id,
        translate=req.translate,
        target_language=req.target_language if req.translate else None,
    )
    job_store.create(job)

    background_tasks.add_task(run_transcription, job_id)

    return TranscribeResponse(job_id=job_id)
