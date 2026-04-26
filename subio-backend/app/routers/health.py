from fastapi import APIRouter

from app.schemas import HealthResponse
from app.settings import settings

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.APP_NAME, version=settings.APP_VERSION)
