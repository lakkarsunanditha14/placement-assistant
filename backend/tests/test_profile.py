"""Profile behaviour, including the never-guess rule."""
from decimal import Decimal

PROFILE = {
    "full_name": "Test Student",
    "email": "test.student@example.com",
    "branch": "CSE",
    "cgpa": "8.10",
    "graduation_year": 2027,
}


def test_patch_leaves_unsent_fields_untouched(client):
    """Omitting a field must not erase it.

    Silently nulling a verified fact because a request didn't mention it
    is a form of guessing, and the eligibility engine would later read
    that null as 'unknown' and produce a wrong answer.
    """
    client.post("/profile", json=PROFILE)

    body = client.patch("/profile", json={"phone": "9999999999"}).json()

    assert body["phone"] == "9999999999"
    assert body["branch"] == "CSE"
    assert Decimal(str(body["cgpa"])) == Decimal("8.10")
    assert body["graduation_year"] == 2027


def test_only_one_profile_can_exist(client):
    client.post("/profile", json=PROFILE)
    assert client.post("/profile", json=PROFILE).status_code == 409


def test_an_impossible_cgpa_is_rejected(client):
    payload = PROFILE | {"cgpa": "11.5"}
    assert client.post("/profile", json=payload).status_code == 422


def test_reading_a_profile_that_does_not_exist_is_404(client):
    assert client.get("/profile").status_code == 404
