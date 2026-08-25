"""Mandatory safety tests — source authorization.

From the Phase 0 baseline:
  - only sources the student explicitly authorized may be read
  - authorization is explicit, never a side effect
"""

SOURCE = {
    "kind": "mock",
    "external_id": "test-group-1",
    "display_name": "Test placement group",
}


def test_registering_a_source_does_not_authorize_it(client):
    response = client.post("/sources", json=SOURCE)
    assert response.status_code == 201

    body = response.json()
    assert body["authorized"] is False
    assert body["is_readable"] is False
    assert body["authorized_at"] is None


def test_explicit_authorization_makes_a_source_readable(client):
    source_id = client.post("/sources", json=SOURCE).json()["id"]

    body = client.post(f"/sources/{source_id}/authorize").json()
    assert body["authorized"] is True
    assert body["is_readable"] is True
    assert body["authorized_at"] is not None


def test_revocation_makes_a_source_unreadable_immediately(client):
    source_id = client.post("/sources", json=SOURCE).json()["id"]
    client.post(f"/sources/{source_id}/authorize")

    body = client.post(f"/sources/{source_id}/revoke").json()
    assert body["authorized"] is False
    assert body["is_readable"] is False
    assert body["revoked_at"] is not None


def test_the_same_source_cannot_be_registered_twice(client):
    client.post("/sources", json=SOURCE)
    assert client.post("/sources", json=SOURCE).status_code == 409


def test_authorizing_an_unknown_source_is_rejected(client):
    assert client.post("/sources/9999/authorize").status_code == 404
