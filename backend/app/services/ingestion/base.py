"""The SourceAdapter contract.

Section 7 of the implementation guide. Every placement source is reached
through this interface, and the rest of the system knows only this interface —
never Telegram-specific details.

The contract is four methods, all of them reads:

    get_source_metadata()
    read_messages()
    read_permitted_attachments()
    normalize_message()

There is no send(), reply(), post(), react(), edit(), delete() or forward().
Adding one would not be a configuration change; it would change what this
system fundamentally is.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SourceMetadata:
    kind: str
    external_id: str
    display_name: str


@dataclass(frozen=True)
class RawAttachment:
    external_id: str
    filename: str
    media_type: str
    size_bytes: int
    content: bytes | None = None


@dataclass(frozen=True)
class RawMessage:
    """Whatever the source gave us, before normalization."""

    external_id: str
    text: str
    posted_at: datetime
    author_display_name: str | None = None
    attachment_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class NormalizedMessage:
    """One message in the shape the rest of the system understands.

    The provenance fields are never dropped. In Phase 10 the system has to
    distinguish 'the message said this' from 'research said this', and that
    is only possible if every fact can be traced back to where it came from.
    """

    source_kind: str
    source_external_id: str
    external_message_id: str
    posted_at: datetime
    fetched_at: datetime

    text: str
    author_display_name: str | None
    attachment_ids: tuple[str, ...]


class SourceAdapter(ABC):
    """Read-only access to one authorized placement source."""

    @abstractmethod
    def get_source_metadata(self) -> SourceMetadata:
        """Identify which source this adapter is bound to."""

    @abstractmethod
    def read_messages(
        self, since: datetime | None = None, limit: int = 100
    ) -> list[RawMessage]:
        """Read messages. Never modifies anything at the source."""

    @abstractmethod
    def read_permitted_attachments(
        self, message_external_id: str
    ) -> list[RawAttachment]:
        """Read only the attachments the student's authorization covers."""

    def normalize_message(
        self, raw: RawMessage, fetched_at: datetime
    ) -> NormalizedMessage:
        """Convert a raw message into the shared shape.

        Concrete on purpose. Every adapter must produce an identical
        structure, so nothing downstream can tell Telegram from the mock —
        which is what makes the mock a real test of the pipeline.
        """
        meta = self.get_source_metadata()
        return NormalizedMessage(
            source_kind=meta.kind,
            source_external_id=meta.external_id,
            external_message_id=raw.external_id,
            posted_at=raw.posted_at,
            fetched_at=fetched_at,
            text=raw.text.strip(),
            author_display_name=raw.author_display_name,
            attachment_ids=raw.attachment_ids,
        )
