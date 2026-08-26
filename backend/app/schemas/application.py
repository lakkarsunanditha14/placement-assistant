"""API contracts for applications."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationState


class ApplicationCreate(BaseModel):
    opportunity_id: int


class ApplicationStateChange(BaseModel):
    to_state: ApplicationState


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opportunity_id: int
    state: ApplicationState
    preparation_approved_at: datetime | None
    submission_approved_at: datetime | None
    outcome_detail: str | None
    created_at: datetime
    updated_at: datetime
