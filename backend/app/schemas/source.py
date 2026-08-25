"""API contracts for authorized placement sources."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.source import SourceKind


class SourceCreate(BaseModel):
    """Registering a source does NOT authorize it.

    There is no `authorized` field here on purpose. Creation and authorization
    are separate acts, because authorization is a decision the student makes
    explicitly — never a side effect of adding a row.
    """

    kind: SourceKind
    external_id: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: SourceKind
    external_id: str
    display_name: str

    authorized: bool
    authorized_at: datetime | None
    revoked_at: datetime | None
    is_readable: bool

    created_at: datetime
    updated_at: datetime
