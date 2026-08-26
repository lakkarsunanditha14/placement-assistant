"""Mandatory safety tests — the two approval gates.

From the Phase 0 baseline:
  - silence is never approval
  - no Gate 1 means no preparation
  - no Gate 2 means no submission
"""
OPPORTUNITY = {"company": "ABC Technologies", "role": "Software Engineer"}


def _application(client) -> dict:
    opportunity_id = client.post(
        "/opportunities", json=OPPORTUNITY).json()["id"]
    return client.post("/applications", json={"opportunity_id": opportunity_id}).json()


def _move(client, application_id: int, to_state: str):
    return client.post(
        f"/applications/{application_id}/state", json={"to_state": to_state}
    )


def test_a_new_application_stops_and_waits(client):
    application = _application(client)
    assert application["state"] == "waiting_for_preparation_approval"
    assert application["preparation_approved_at"] is None


def test_doing_nothing_never_becomes_approval(client):
    """The whole point. Re-reading an application changes nothing about it."""
    application = _application(client)

    for _ in range(3):
        current = client.get(f"/applications/{application['id']}").json()

    assert current["state"] == "waiting_for_preparation_approval"
    assert current["preparation_approved_at"] is None


def test_preparing_cannot_be_reached_without_gate_one(client):
    application = _application(client)
    assert _move(client, application["id"], "preparing").status_code == 400


def test_submitting_cannot_be_reached_without_gate_two(client):
    application = _application(client)
    assert _move(client, application["id"], "submitting").status_code == 400


def test_the_workflow_cannot_be_skipped_to_submitted(client):
    application = _application(client)
    assert _move(client, application["id"], "submitted").status_code == 409


def test_gate_two_is_refused_before_the_form_is_reviewed(client):
    """An application still waiting on Gate 1 cannot be submitted."""
    application = _application(client)
    response = client.post(
        f"/applications/{application['id']}/approve-submission"
    )
    assert response.status_code == 409


def test_gate_one_records_when_it_was_given(client):
    application = _application(client)

    body = client.post(
        f"/applications/{application['id']}/approve-preparation"
    ).json()

    assert body["state"] == "preparing"
    assert body["preparation_approved_at"] is not None


def test_gate_one_cannot_be_given_twice(client):
    application = _application(client)
    client.post(f"/applications/{application['id']}/approve-preparation")

    second = client.post(
        f"/applications/{application['id']}/approve-preparation")
    assert second.status_code == 409


def test_the_full_path_needs_both_approvals(client):
    application_id = _application(client)["id"]

    client.post(
        f"/applications/{application_id}/approve-preparation")  # Gate 1
    _move(client, application_id, "questions_pending")
    _move(client, application_id, "validating")
    _move(client, application_id, "ready_for_review")
    _move(client, application_id, "waiting_for_submission_approval")

    body = client.post(
        f"/applications/{application_id}/approve-submission").json()  # Gate 2

    assert body["state"] == "submitting"
    assert body["preparation_approved_at"] is not None
    assert body["submission_approved_at"] is not None


def test_a_submitted_application_is_terminal(client):
    application_id = _application(client)["id"]
    client.post(f"/applications/{application_id}/approve-preparation")
    _move(client, application_id, "validating")
    _move(client, application_id, "ready_for_review")
    _move(client, application_id, "waiting_for_submission_approval")
    client.post(f"/applications/{application_id}/approve-submission")
    _move(client, application_id, "submitted")

    assert _move(client, application_id, "ready_for_review").status_code == 409


def test_one_application_per_opportunity(client):
    opportunity_id = client.post(
        "/opportunities", json=OPPORTUNITY).json()["id"]
    client.post("/applications", json={"opportunity_id": opportunity_id})

    second = client.post(
        "/applications", json={"opportunity_id": opportunity_id})
    assert second.status_code == 409
