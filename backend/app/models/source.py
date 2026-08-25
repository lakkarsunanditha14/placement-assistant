"""Authorized placement sources.

Read-only by construction. A source must exist in this table with
authorized=True before any ingestion code may read from it.

There is deliberately NO column, flag or field anywhere in this model that
could enable writing back to a source. Sending, replying, posting, reacting,
editing, deleting and forwarding are not features that are switched off —
they are capabilities this system never has.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SourceKind(str, enum.Enum):
    """Which adapter reads this source. MOCK is for tests (Phase 3)."""

    MOCK = "mock"
    TELEGRAM = "telegram"


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("kind", "external_id",
                         name="uq_source_kind_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    kind: Mapped[SourceKind] = mapped_column(
        Enum(SourceKind, name="source_kind"))
    external_id: Mapped[str] = mapped_column(String(200))
    display_name: Mapped[str] = mapped_column(String(200))

    # Authorization is explicit and revocable. Default is False:
    # a source that merely exists is not a source you may read.
    authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    authorized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def is_readable(self) -> bool:
        """The single check every ingestion path must pass through."""
        return self.authorized and self.revoked_at is None
