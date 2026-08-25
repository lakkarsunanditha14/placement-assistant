"""The only way to obtain a SourceAdapter.

Nothing constructs an adapter directly. Every read passes through here, which
means the authorization check exists in exactly one place and cannot be
forgotten by a future caller.
"""
from datetime import datetime

from app.models import Source
from app.models.source import SourceKind
from app.services.ingestion.base import NormalizedMessage, SourceAdapter
from app.services.ingestion.mock import MockSourceAdapter


class SourceNotAuthorizedError(RuntimeError):
    """Raised when something attempts to read a source it may not read."""


class UnsupportedSourceKindError(RuntimeError):
    """Raised when no adapter exists for a source's kind."""


# Phase 4 adds SourceKind.TELEGRAM here. Until then, attempting to read a
# Telegram source fails loudly rather than silently doing nothing.
ADAPTERS: dict[SourceKind, type[SourceAdapter]] = {
    SourceKind.MOCK: MockSourceAdapter,
}


def get_adapter_for(source: Source) -> SourceAdapter:
    """Return a read-only adapter for an authorized source.

    Raises rather than returning None. A caller that forgets to check a
    return value would silently read nothing; a caller that ignores an
    exception cannot.
    """
    if not source.is_readable:
        raise SourceNotAuthorizedError(
            f"Source {source.id} ({source.display_name}) is not authorized "
            "for reading. Authorization must be granted explicitly."
        )

    try:
        adapter_class = ADAPTERS[source.kind]
    except KeyError:
        raise UnsupportedSourceKindError(
            f"No adapter is registered for source kind '{source.kind}'."
        ) from None

    return adapter_class(
        external_id=source.external_id,
        display_name=source.display_name,
    )


def read_normalized_messages(
    source: Source,
    fetched_at: datetime,
    since: datetime | None = None,
    limit: int = 100,
) -> list[NormalizedMessage]:
    """Read and normalize in one guarded call.

    This is what Phase 5 will use to store messages, and what Phase 4 will
    point at a real Telegram group. The authorization check happens first,
    every time, because get_adapter_for is the only door in.
    """
    adapter = get_adapter_for(source)
    raw_messages = adapter.read_messages(since=since, limit=limit)
    return [adapter.normalize_message(raw, fetched_at) for raw in raw_messages]
