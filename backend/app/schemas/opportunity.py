"""API contracts for placement opportunities."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OpportunityBase(BaseModel):
    message_id: int | None = None

    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    technical: bool | None = None
    package: str | None = Field(default=None, max_length=100)
    apply_url: str | None = Field(default=None, max_length=1000)
    bond: str | None = Field(default=None, max_length=500)
    instructions: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    deadline: datetime | None = None

    # None means the message did not state this requirement.
    eligible_branches: list[str] | None = None
    min_cgpa: Decimal | None = Field(default=None, ge=0, le=10)
    eligible_graduation_year: int | None = Field(
        default=None, ge=1900, le=2100)
    active_backlogs_allowed: bool | None = None


class OpportunityCreate(OpportunityBase):
    """Created by hand now; by Claude in Phase 6. Same shape either way."""


class OpportunityRead(OpportunityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class RuleResultRead(BaseModel):
    rule: str
    outcome: str
    explanation: str


class EligibilityRead(BaseModel):
    opportunity_id: int
    verdict: str
    rules: list[RuleResultRead]
