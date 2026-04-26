import logging
from pathlib import Path

from app.presets import PRESETS_BY_ID
from app.settings import settings
from app.services import storage
from app.services.ffmpeg import probe_duration, extract_audio, FFmpegError
from app.services.job_store import Job, JobOutputs, job_store
from app.services.srt import build_srt, validate_srt
from app.services.translation import TranslationError, translate_outputs
from app.services.txt import build_txt
from app.services.whisper_engine import transcribe as whisper_transcribe

logger = logging.getLogger("subio.pipeline")


def _set(job_id: str, **fields) -> None:
    job_store.update(job_id, **fields)


def _safe_error(message: str) -> str:
    return message[:200] if message else "Internal error"


def run_transcription(job_id: str) -> None:
    job: Job | None = job_store.get(job_id)
    if job is None:
        return

    upload = storage.upload_registry.get(job.upload_id)
    if upload is None:
        _set(job_id, status="failed", error="Upload not found", progress=0.0)
        return

    preset = PRESETS_BY_ID.get(job.preset_id)
    if preset is None:
        _set(job_id, status="failed", error="Invalid preset", progress=0.0)
        return

    audio_path: Path = storage.AUDIO_DIR / f"{job.upload_id}.wav"
    txt_path: Path | None = None
    srt_path: Path | None = None
    tr_txt_path: Path | None = None
    tr_srt_path: Path | None = None

    try:
        _set(job_id, status="extracting_audio", progress=0.1)
        extract_audio(upload.path, audio_path)

        _set(job_id, progress=0.2)
        audio_duration = probe_duration(audio_path)
        if audio_duration > settings.max_audio_duration_seconds:
            storage.safe_remove(audio_path)
            _set(
                job_id,
                status="failed",
                error=f"Audio exceeds {settings.MAX_AUDIO_DURATION_MINUTES} minutes",
                progress=0.0,
            )
            return

        _set(job_id, status="transcribing", progress=0.3)
        result = whisper_transcribe(audio_path, job.language)
        segments = result.get("segments", [])
        full_text = result.get("text", "")

        _set(job_id, status="generating", progress=0.85)
        txt_body = build_txt(segments, full_text)
        srt_body = build_srt(segments, preset)
        if not srt_body.strip():
            raise ValueError("Transcription produced no subtitle content")
        validate_srt(srt_body)

        base_name = upload.sanitized_filename.rsplit(".", 1)[0] or "subio"
        txt_filename = f"subio_{base_name}.txt"
        srt_filename = f"subio_{base_name}.srt"

        txt_id = storage.new_id()
        srt_id = storage.new_id()
        txt_path = storage.OUTPUTS_DIR / f"{txt_id}.txt"
        srt_path = storage.OUTPUTS_DIR / f"{srt_id}.srt"

        txt_path.write_text(txt_body, encoding="utf-8")
        srt_path.write_text(srt_body, encoding="utf-8")

        storage.file_registry.register(
            txt_id,
            storage.FileEntry(path=txt_path, filename=txt_filename, mime="text/plain", kind="txt"),
        )
        storage.file_registry.register(
            srt_id,
            storage.FileEntry(path=srt_path, filename=srt_filename, mime="application/x-subrip", kind="srt"),
        )

        outputs = JobOutputs(
            txt_file_id=txt_id,
            txt_filename=txt_filename,
            srt_file_id=srt_id,
            srt_filename=srt_filename,
        )

        if job.translate and job.target_language:
            _set(job_id, status="translating", progress=0.92)
            tr_srt_body, tr_txt_body = translate_outputs(srt_body, job.target_language)

            tr_txt_id = storage.new_id()
            tr_srt_id = storage.new_id()
            tr_txt_filename = f"subio_{base_name}.{job.target_language}.txt"
            tr_srt_filename = f"subio_{base_name}.{job.target_language}.srt"
            tr_txt_path = storage.OUTPUTS_DIR / f"{tr_txt_id}.txt"
            tr_srt_path = storage.OUTPUTS_DIR / f"{tr_srt_id}.srt"

            tr_txt_path.write_text(tr_txt_body, encoding="utf-8")
            tr_srt_path.write_text(tr_srt_body, encoding="utf-8")

            storage.file_registry.register(
                tr_txt_id,
                storage.FileEntry(path=tr_txt_path, filename=tr_txt_filename, mime="text/plain", kind="txt"),
            )
            storage.file_registry.register(
                tr_srt_id,
                storage.FileEntry(path=tr_srt_path, filename=tr_srt_filename, mime="application/x-subrip", kind="srt"),
            )

            outputs.translated_txt_file_id = tr_txt_id
            outputs.translated_txt_filename = tr_txt_filename
            outputs.translated_srt_file_id = tr_srt_id
            outputs.translated_srt_filename = tr_srt_filename

        _set(job_id, status="done", progress=1.0, outputs=outputs)
    except FFmpegError as e:
        logger.exception("ffmpeg failed for job %s", job_id)
        for p in (txt_path, srt_path, tr_txt_path, tr_srt_path):
            if p:
                storage.safe_remove(p)
        _set(job_id, status="failed", error="Audio processing failed", progress=0.0)
    except TranslationError as e:
        logger.exception("translation failed for job %s", job_id)
        for p in (tr_txt_path, tr_srt_path):
            if p:
                storage.safe_remove(p)
        _set(job_id, status="failed", error=f"Translation failed: {_safe_error(str(e))}", progress=0.0)
    except Exception as e:
        logger.exception("transcription pipeline failed for job %s", job_id)
        for p in (txt_path, srt_path, tr_txt_path, tr_srt_path):
            if p:
                storage.safe_remove(p)
        _set(job_id, status="failed", error=_safe_error(str(e)), progress=0.0)
    finally:
        storage.safe_remove(audio_path)
