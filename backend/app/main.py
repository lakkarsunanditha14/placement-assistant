"""FastAPI entrypoint for the Placement Assistant backend."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="Phase 5: message storage. Telegram deferred; ingestion runs on the mock adapter.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root() -> dict:
    return {"service": settings.project_name, "phase": 11, "docs": "/docs"}
