"""The eligibility endpoint: real rows in, explainable verdict out."""

PROFILE = {
    "full_name": "Test Student",
    "email": "eligibility.test@example.com",
    "branch": "CSE",
    "cgpa": "8.10",
    "graduation_year": 2027,
    "active_backlogs": 0,
}

OPPORTUNITY = {
    "company": "ABC Technologies",
    "role": "Software Engineer",
    "technical": True,
    "package": "8 LPA",
    "eligible_branches": ["CSE", "IT"],
    "min_cgpa": "7.0",
    "eligible_graduation_year": 2027,
    "active_backlogs_allowed": False,
}


def _opportunity_id(client, **overrides) -> int:
    return client.post("/opportunities", json=OPPORTUNITY | overrides).json()["id"]


def test_eligibility_requires_a_profile(client):
    """Without a trusted profile there is nothing to compare against,
    and inventing one would be a guess."""
    opportunity_id = _opportunity_id(client)
    assert client.get(
        f"/opportunities/{opportunity_id}/eligibility").status_code == 409


def test_a_qualifying_student_is_eligible(client):
    client.post("/profile", json=PROFILE)
    opportunity_id = _opportunity_id(client)

    body = client.get(f"/opportunities/{opportunity_id}/eligibility").json()

    assert body["verdict"] == "eligible"
    assert len(body["rules"]) == 4
    assert all(r["outcome"] == "pass" for r in body["rules"])


def test_the_verdict_carries_its_reasoning(client):
    client.post("/profile", json=PROFILE)
    opportunity_id = _opportunity_id(client)

    rules = client.get(
        f"/opportunities/{opportunity_id}/eligibility").json()["rules"]
    cgpa = next(r for r in rules if r["rule"] == "cgpa")

    assert cgpa["explanation"] == "CGPA 8.10 >= required 7.00"


def test_falling_short_is_not_eligible(client):
    client.post("/profile", json=PROFILE)
    opportunity_id = _opportunity_id(client, min_cgpa="9.0")

    body = client.get(f"/opportunities/{opportunity_id}/eligibility").json()
    assert body["verdict"] == "not_eligible"


def test_a_missing_profile_field_needs_review(client):
    client.post("/profile", json=PROFILE | {"cgpa": None})
    opportunity_id = _opportunity_id(client)

    body = client.get(f"/opportunities/{opportunity_id}/eligibility").json()
    assert body["verdict"] == "needs_review"


def test_an_unstated_requirement_produces_no_rule(client):
    client.post("/profile", json=PROFILE)
    opportunity_id = _opportunity_id(
        client,
        eligible_branches=None,
        eligible_graduation_year=None,
        active_backlogs_allowed=None,
    )

    rules = client.get(
        f"/opportunities/{opportunity_id}/eligibility").json()["rules"]
    assert [r["rule"] for r in rules] == ["cgpa"]
