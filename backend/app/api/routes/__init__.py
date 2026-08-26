from fastapi import APIRouter

from app.api.routes import health, opportunities, profile, sources

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(sources.router)
api_router.include_router(opportunities.router)
