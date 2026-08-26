"""A placement opportunity extracted from a message.

Phase 6 will populate these rows from Claude. Until then they are created
by hand through the API — deliberately, because it keeps the storage and
the extraction separable. Nothing downstream cares which one filled the row.

Requirement columns are nullable on purpose. NULL means "the message did
not say", which is not the same as "no constraint" and never the same as
a guess.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Provenance: which message this came from, if any.
    message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), default=None, index=True
    )

    company: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200))
    technical: Mapped[bool | None] = mapped_column(Boolean, default=None)
    package: Mapped[str | None] = mapped_column(String(100), default=None)
    apply_url: Mapped[str | None] = mapped_column(String(1000), default=None)
    bond: Mapped[str | None] = mapped_column(String(500), default=None)
    instructions: Mapped[str | None] = mapped_column(Text, default=None)
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    skills: Mapped[list] = mapped_column(JSONB, default=list)
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Stated eligibility requirements. NULL = not stated.
    eligible_branches: Mapped[list | None] = mapped_column(JSONB, default=None)
    min_cgpa: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), default=None)
    eligible_graduation_year: Mapped[int | None] = mapped_column(
        Integer, default=None)
    active_backlogs_allowed: Mapped[bool |
                                    None] = mapped_column(Boolean, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
