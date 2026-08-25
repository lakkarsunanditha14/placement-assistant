"""API contracts for the trusted student profile.

Validation here is deliberate: these values feed the deterministic eligibility
engine in Phase 7, so a malformed CGPA must be rejected at the edge rather
than silently producing a wrong eligibility answer later.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentProfileBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)

    college: str | None = Field(default=None, max_length=200)
    branch: str | None = Field(default=None, max_length=100)
    cgpa: Decimal | None = Field(default=None, ge=0, le=10)
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    active_backlogs: int | None = Field(default=None, ge=0)

    skills: list[str] = Field(default_factory=list)
    links: dict[str, str] = Field(default_factory=dict)
    resume_path: str | None = Field(default=None, max_length=500)


class StudentProfileCreate(StudentProfileBase):
    """Everything needed to create the profile."""


class StudentProfileUpdate(BaseModel):
    """Partial update. Only the fields actually sent are changed.

    A field left out is untouched — it is NOT reset to null. Silently
    erasing a verified fact would be a form of guessing.
    """

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    college: str | None = Field(default=None, max_length=200)
    branch: str | None = Field(default=None, max_length=100)
    cgpa: Decimal | None = Field(default=None, ge=0, le=10)
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    active_backlogs: int | None = Field(default=None, ge=0)
    skills: list[str] | None = None
    links: dict[str, str] | None = None
    resume_path: str | None = Field(default=None, max_length=500)


class StudentProfileRead(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
