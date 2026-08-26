"""Stored placement messages.

One row per message per source. Provenance is not optional here: every fact
the system later asserts must be traceable to the message it came from, and
the message traceable to the authorized source it was read from.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        # Re-reading a source must never duplicate a message.
        UniqueConstraint("source_id", "external_id",
                         name="uq_message_source_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(200))

    text: Mapped[str] = mapped_column(Text)
    author_display_name: Mapped[str | None] = mapped_column(
        String(200), default=None
    )
    attachment_ids: Mapped[list] = mapped_column(JSONB, default=list)

    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"),
        default=ProcessingStatus.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
