"""Application settings. Loaded once from the repo-root .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> core -> app -> backend -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    log_level: str = "INFO"
    project_name: str = "AI-Powered Personal Placement Assistant"

    database_url: str = (
        "postgresql+psycopg2://placement:placement@localhost:5432/placement_assistant"
    )

    # Filled in at later phases. Never logged, never sent to the frontend.
    anthropic_api_key: str = ""
    telegram_api_id: str = ""
    telegram_api_hash: str = ""

    # CORS: the Next.js dev server
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
