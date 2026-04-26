from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class LanguageItem(BaseModel):
    code: str
    name: str


class TargetLanguageItem(BaseModel):
    code: str
    label: str


class LanguagesResponse(BaseModel):
    languages: list[LanguageItem]
    translation_available: bool
    supported_target_languages: list[TargetLanguageItem]


class PresetItem(BaseModel):
    id: str
    name: str
    max_words_per_line: int
    max_lines_per_block: int
    max_chars_per_line: int
    max_words_per_cue: int
    min_duration: float
    max_duration: float


class PresetsResponse(BaseModel):
    presets: list[PresetItem]


class PlanItem(BaseModel):
    id: str
    name: str
    price_label: str
    price_eur: int
    billing_interval: str
    target_user: str
    positioning: str
    max_upload_size_mb: int
    max_video_duration_minutes: int
    max_audio_duration_minutes: int
    max_outputs_per_job: int
    output_summary: str
    included_outputs: list[str]
    subio_ai_available: bool
    ads_placeholder: bool
    subscription_placeholder: bool
    ads_available: bool
    subscription_available: bool


class PlansResponse(BaseModel):
    plans: list[PlanItem]


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    size_bytes: int
    duration_seconds: float


class TranscribeRequest(BaseModel):
    upload_id: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    preset_id: str = Field(..., min_length=1)
    translate: bool = False
    target_language: Optional[str] = None


class TranscribeResponse(BaseModel):
    job_id: str


class OutputFile(BaseModel):
    file_id: str
    filename: str


class JobOutputs(BaseModel):
    txt: OutputFile
    srt: OutputFile
    translated_txt: Optional[OutputFile] = None
    translated_srt: Optional[OutputFile] = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    error: Optional[str] = None
    outputs: Optional[JobOutputs] = None
