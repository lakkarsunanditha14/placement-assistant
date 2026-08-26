"""Ingestion behaviour: authorization, idempotency, provenance."""
from sqlalchemy import select

from app.models import Message, ProcessingStatus

SOURCE = {
    "kind": "mock",
    "external_id": "ingest-test-group",
    "display_name": "Ingest Test Group",
}


def _register(client) -> int:
    return client.post("/sources", json=SOURCE).json()["id"]


def _register_and_authorize(client) -> int:
    source_id = _register(client)
    client.post(f"/sources/{source_id}/authorize")
    return source_id


def test_ingesting_an_unauthorized_source_is_forbidden(client):
    source_id = _register(client)
    assert client.post(f"/sources/{source_id}/ingest").status_code == 403


def test_ingesting_a_revoked_source_is_forbidden(client):
    source_id = _register_and_authorize(client)
    client.post(f"/sources/{source_id}/revoke")
    assert client.post(f"/sources/{source_id}/ingest").status_code == 403


def test_first_ingest_stores_every_message(client):
    source_id = _register_and_authorize(client)
    assert client.post(f"/sources/{source_id}/ingest").json() == {
        "read": 7,
        "stored": 7,
        "skipped": 0,
    }


def test_repeated_ingest_stores_nothing_new(client):
    """The scheduler in Phase 8 re-reads on a timer. A duplicate message
    would mean a duplicate reminder, or a second application."""
    source_id = _register_and_authorize(client)
    client.post(f"/sources/{source_id}/ingest")

    assert client.post(f"/sources/{source_id}/ingest").json() == {
        "read": 7,
        "stored": 0,
        "skipped": 7,
    }


def test_stored_messages_keep_their_provenance(client, db_session):
    source_id = _register_and_authorize(client)
    client.post(f"/sources/{source_id}/ingest")

    message = db_session.execute(
        select(Message).where(
            Message.source_id == source_id, Message.external_id == "m-005"
        )
    ).scalar_one()

    assert message.status == ProcessingStatus.PENDING
    assert message.attachment_ids == ["a-001"]
    assert message.posted_at < message.fetched_at
    assert message.author_display_name == "Placement Cell"
