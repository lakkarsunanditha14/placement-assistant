"""An application in progress.

State lives in the database, not in memory, so a crash or restart can never
resume in the wrong place — and can never re-submit something already sent.
"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApplicationState(str, enum.Enum):
    DETECTED = "detected"
    SUMMARY_READY = "summary_ready"
    WAITING_FOR_PREPARATION_APPROVAL = "waiting_for_preparation_approval"
    PREPARING = "preparing"
    QUESTIONS_PENDING = "questions_pending"
    VALIDATING = "validating"
    READY_FOR_REVIEW = "ready_for_review"
    WAITING_FOR_SUBMISSION_APPROVAL = "waiting_for_submission_approval"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"
    FAILED = "failed"
    MANUAL_ACTION_REQUIRED = "manual_action_required"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # One application per opportunity. The unique constraint is the last
    # line of defence against applying to the same job twice.
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True, index=True
    )

    state: Mapped[ApplicationState] = mapped_column(
        Enum(ApplicationState, name="application_state"),
        default=ApplicationState.DETECTED,
    )

    # Timestamps, not booleans: an approval is an event that happened at a
    # moment, and the audit log needs to say when.
    preparation_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    submission_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    outcome_detail: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
