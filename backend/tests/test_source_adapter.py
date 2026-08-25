"""Mandatory safety tests — the adapter contract.

From the Phase 0 baseline:
  - unauthorized source is rejected
  - no source write operation exists anywhere in the codebase
"""
from datetime import datetime, timezone

import pytest

from app.models import Source
from app.models.source import SourceKind
from app.services.ingestion.base import SourceAdapter
from app.services.ingestion.mock import MockSourceAdapter
from app.services.ingestion.reader import (
    SourceNotAuthorizedError,
    get_adapter_for,
    read_normalized_messages,
)

FETCHED_AT = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)


def _source(*, authorized: bool, revoked_at: datetime | None = None) -> Source:
    """An unsaved Source. No database needed — authorization is a property
    of the object, so it can be checked without one."""
    return Source(
        kind=SourceKind.MOCK,
        external_id="mock-placement-group",
        display_name="Mock Placement Group",
        authorized=authorized,
        revoked_at=revoked_at,
    )


def test_an_unauthorized_source_cannot_be_read():
    with pytest.raises(SourceNotAuthorizedError):
        get_adapter_for(_source(authorized=False))


def test_a_revoked_source_cannot_be_read():
    with pytest.raises(SourceNotAuthorizedError):
        get_adapter_for(_source(authorized=True, revoked_at=FETCHED_AT))


def test_the_reading_helper_also_refuses_an_unauthorized_source():
    """The guard must hold on every path in, not just the obvious one."""
    with pytest.raises(SourceNotAuthorizedError):
        read_normalized_messages(
            _source(authorized=False), fetched_at=FETCHED_AT)


def test_an_authorized_source_yields_messages():
    messages = read_normalized_messages(
        _source(authorized=True), fetched_at=FETCHED_AT
    )
    assert len(messages) == 7
    assert messages[0].external_message_id == "m-001"


def test_normalization_preserves_provenance():
    message = read_normalized_messages(
        _source(authorized=True), fetched_at=FETCHED_AT
    )[0]

    assert message.source_kind == "mock"
    assert message.source_external_id == "mock-placement-group"
    assert message.external_message_id == "m-001"
    assert message.fetched_at == FETCHED_AT
    assert message.posted_at < message.fetched_at


def test_since_excludes_messages_already_seen():
    everything = read_normalized_messages(
        _source(authorized=True), fetched_at=FETCHED_AT
    )
    cutoff = everything[2].posted_at

    newer = read_normalized_messages(
        _source(authorized=True), fetched_at=FETCHED_AT, since=cutoff
    )

    assert [m.external_message_id for m in newer] == [
        m.external_message_id for m in everything[3:]
    ]


WRITE_WORDS = ("send", "reply", "post", "react", "edit", "delete", "forward")


def test_the_adapter_contract_exposes_no_write_operations():
    """Reads the classes themselves, not their behaviour.

    If anyone adds a write method to the contract or to any adapter, this
    fails before that code can ever reach a real placement group.
    """
    for klass in (SourceAdapter, MockSourceAdapter):
        for attribute in dir(klass):
            if attribute.startswith("_"):
                continue
            for word in WRITE_WORDS:
                assert word not in attribute.lower(), (
                    f"{klass.__name__}.{attribute} suggests a write operation. "
                    "Placement sources are read-only."
                )
