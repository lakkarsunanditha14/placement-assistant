"""Trusted student profile — verified facts only.

Every field here is entered by the student or left empty. Nothing in this
table is ever inferred, guessed or filled in by AI. When a field is null,
the correct behaviour is to ask the user, never to invent a value.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identity
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), default=None)

    # Academic facts — used by the deterministic eligibility engine in Phase 7
    college: Mapped[str | None] = mapped_column(String(200), default=None)
    branch: Mapped[str | None] = mapped_column(String(100), default=None)
    cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=None)
    graduation_year: Mapped[int | None] = mapped_column(Integer, default=None)
    active_backlogs: Mapped[int | None] = mapped_column(Integer, default=None)

    # Flexible fields
    skills: Mapped[list] = mapped_column(JSONB, default=list)
    links: Mapped[dict] = mapped_column(JSONB, default=dict)
    resume_path: Mapped[str | None] = mapped_column(String(500), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
