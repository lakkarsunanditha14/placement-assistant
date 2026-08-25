"""Health endpoints. Phase 1 definition of done is verified through these."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness() -> dict:
    """Process is up. Does not touch the database."""
    settings = get_settings()
    return {"status": "ok", "app": settings.project_name, "env": settings.app_env}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)) -> dict:
    """Process is up AND PostgreSQL answers."""
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
        status = "ok"
    except Exception as exc:
        database = f"unavailable: {type(exc).__name__}"
        status = "degraded"
    return {"status": status, "database": database}
