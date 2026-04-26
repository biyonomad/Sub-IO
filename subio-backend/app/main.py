import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request

from app.errors import error_response
from app.routers import config as config_router
from app.routers import files as files_router
from app.routers import health as health_router
from app.routers import jobs as jobs_router
from app.routers import transcribe as transcribe_router
from app.routers import upload as upload_router
from app.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger("subio").exception("Unhandled error: %s", exc)
    return error_response(HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "Internal server error"}))


app.include_router(health_router.router)
app.include_router(config_router.router)
app.include_router(upload_router.router)
app.include_router(transcribe_router.router)
app.include_router(jobs_router.router)
app.include_router(files_router.router)
