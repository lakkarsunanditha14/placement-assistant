"""Store normalized messages.

Idempotent by design: re-reading a source never duplicates a message. That
matters because Phase 8's scheduler will re-read on a timer, and a duplicate
opportunity would mean a duplicate reminder — or worse, a second application.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Message, Source
from app.services.ingestion.reader import read_normalized_messages


def ingest_source(
    db: Session, source: Source, fetched_at: datetime, limit: int = 100
) -> dict[str, int]:
    """Read an authorized source and store whatever is not already stored.

    Raises SourceNotAuthorizedError via read_normalized_messages if the
    source may not be read. The guard is not repeated here on purpose —
    one door in.
    """
    normalized = read_normalized_messages(
        source, fetched_at=fetched_at, limit=limit)

    already_stored = set(
        db.execute(
            select(Message.external_id).where(Message.source_id == source.id)
        ).scalars()
    )

    fresh = [m for m in normalized if m.external_message_id not in already_stored]

    db.add_all(
        Message(
            source_id=source.id,
            external_id=m.external_message_id,
            text=m.text,
            author_display_name=m.author_display_name,
            attachment_ids=list(m.attachment_ids),
            posted_at=m.posted_at,
            fetched_at=m.fetched_at,
        )
        for m in fresh
    )
    db.commit()

    return {
        "read": len(normalized),
        "stored": len(fresh),
        "skipped": len(normalized) - len(fresh),
    }
