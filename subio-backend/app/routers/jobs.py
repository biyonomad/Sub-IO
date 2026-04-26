from fastapi import APIRouter

from app import errors
from app.schemas import JobOutputs, JobResponse, OutputFile
from app.services.job_store import job_store

router = APIRouter()


@router.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = job_store.get(job_id)
    if job is None:
        raise errors.job_not_found()

    outputs = None
    if job.outputs is not None:
        translated_txt = None
        translated_srt = None
        if job.outputs.translated_txt_file_id and job.outputs.translated_txt_filename:
            translated_txt = OutputFile(
                file_id=job.outputs.translated_txt_file_id,
                filename=job.outputs.translated_txt_filename,
            )
        if job.outputs.translated_srt_file_id and job.outputs.translated_srt_filename:
            translated_srt = OutputFile(
                file_id=job.outputs.translated_srt_file_id,
                filename=job.outputs.translated_srt_filename,
            )
        outputs = JobOutputs(
            txt=OutputFile(file_id=job.outputs.txt_file_id, filename=job.outputs.txt_filename),
            srt=OutputFile(file_id=job.outputs.srt_file_id, filename=job.outputs.srt_filename),
            translated_txt=translated_txt,
            translated_srt=translated_srt,
        )

    return JobResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        error=job.error,
        outputs=outputs,
    )
