from fastapi import APIRouter

from app.languages import SUPPORTED_LANGUAGES, SUPPORTED_TARGET_LANGUAGES
from app.presets import PRESETS
from app.schemas import LanguagesResponse, PresetsResponse, PlanItem, PlansResponse
from app.settings import settings

router = APIRouter()


@router.get("/api/config/languages", response_model=LanguagesResponse)
def languages() -> LanguagesResponse:
    return LanguagesResponse(
        languages=SUPPORTED_LANGUAGES,
        translation_available=bool(settings.ENABLE_TRANSLATION and settings.OPENAI_API_KEY),
        supported_target_languages=SUPPORTED_TARGET_LANGUAGES,
    )


@router.get("/api/config/presets", response_model=PresetsResponse)
def presets() -> PresetsResponse:
    return PresetsResponse(presets=PRESETS)


@router.get("/api/config/plans", response_model=PlansResponse)
def plans() -> PlansResponse:
    local_plan = PlanItem(
        id="local",
        name="Local",
        price_label="Personal use",
        price_eur=0,
        billing_interval="local",
        target_user="Personal",
        positioning="Local personal video-to-text and SRT subtitle tool",
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_video_duration_minutes=settings.MAX_VIDEO_DURATION_MINUTES,
        max_audio_duration_minutes=settings.MAX_AUDIO_DURATION_MINUTES,
        max_outputs_per_job=2,
        output_summary="TXT + SRT",
        included_outputs=["TXT", "SRT"],
        subio_ai_available=False,
        ads_placeholder=False,
        subscription_placeholder=False,
        ads_available=False,
        subscription_available=False,
    )
    return PlansResponse(plans=[local_plan])
