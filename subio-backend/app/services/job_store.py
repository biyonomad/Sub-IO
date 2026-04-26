import threading
import time
from dataclasses import dataclass, field
from typing import Optional


JOB_STATUSES = (
    "queued",
    "extracting_audio",
    "transcribing",
    "generating",
    "translating",
    "done",
    "failed",
)


@dataclass
class JobOutputs:
    txt_file_id: str
    txt_filename: str
    srt_file_id: str
    srt_filename: str
    translated_txt_file_id: Optional[str] = None
    translated_txt_filename: Optional[str] = None
    translated_srt_file_id: Optional[str] = None
    translated_srt_filename: Optional[str] = None


@dataclass
class Job:
    id: str
    upload_id: str
    language: str
    preset_id: str
    translate: bool = False
    target_language: Optional[str] = None
    status: str = "queued"
    progress: float = 0.0
    error: Optional[str] = None
    outputs: Optional[JobOutputs] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()

    def create(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for k, v in fields.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            job.updated_at = time.time()
            return job


job_store = JobStore()
