"""The eligibility engine is deterministic and explainable.

These tests are the reason Claude never gets to decide eligibility: every
case here has exactly one correct answer, provable by reading the numbers.
"""
from dataclasses import dataclass
from decimal import Decimal

from app.services.eligibility.evaluator import (
    Eligibility,
    Requirements,
    RuleOutcome,
    evaluate,
)


@dataclass
class Profile:
    """A stand-in for StudentProfile. No database needed."""

    branch: str | None = "CSE"
    cgpa: Decimal | None = Decimal("8.10")
    graduation_year: int | None = 2027
    active_backlogs: int | None = 0


FULL = Requirements(
    branches=("CSE", "IT"),
    min_cgpa=Decimal("7.0"),
    graduation_year=2027,
    active_backlogs_allowed=False,
)


def test_a_qualifying_student_is_eligible():
    result = evaluate(FULL, Profile())
    assert result.verdict is Eligibility.ELIGIBLE
    assert len(result.rules) == 4
    assert all(r.outcome is RuleOutcome.PASS for r in result.rules)


def test_cgpa_comparison_is_exact():
    """8.10 >= 7.0 must be arithmetic, not judgement."""
    result = evaluate(FULL, Profile())
    cgpa_rule = next(r for r in result.rules if r.rule == "cgpa")
    assert cgpa_rule.explanation == "CGPA 8.10 >= required 7.0"


def test_exactly_meeting_the_cgpa_bar_passes():
    result = evaluate(FULL, Profile(cgpa=Decimal("7.00")))
    assert result.verdict is Eligibility.ELIGIBLE


def test_falling_short_on_cgpa_is_not_eligible():
    result = evaluate(FULL, Profile(cgpa=Decimal("6.99")))
    assert result.verdict is Eligibility.NOT_ELIGIBLE


def test_wrong_branch_is_not_eligible():
    result = evaluate(FULL, Profile(branch="ECE"))
    assert result.verdict is Eligibility.NOT_ELIGIBLE


def test_branch_matching_ignores_case():
    assert evaluate(FULL, Profile(branch="cse")
                    ).verdict is Eligibility.ELIGIBLE


def test_an_active_backlog_is_not_eligible():
    result = evaluate(FULL, Profile(active_backlogs=1))
    assert result.verdict is Eligibility.NOT_ELIGIBLE


def test_a_missing_profile_field_needs_review_not_a_guess():
    """An absent CGPA is unknown. It is never assumed to pass or fail."""
    result = evaluate(FULL, Profile(cgpa=None))
    assert result.verdict is Eligibility.NEEDS_REVIEW

    cgpa_rule = next(r for r in result.rules if r.rule == "cgpa")
    assert cgpa_rule.outcome is RuleOutcome.UNKNOWN


def test_a_definite_failure_outranks_an_unknown():
    """Wrong branch is disqualifying whether or not the CGPA is known."""
    result = evaluate(FULL, Profile(branch="ECE", cgpa=None))
    assert result.verdict is Eligibility.NOT_ELIGIBLE


def test_a_requirement_the_message_never_stated_is_not_a_rule():
    """Silence in the message is not a constraint, in either direction."""
    result = evaluate(Requirements(min_cgpa=Decimal("7.0")),
                      Profile(branch="ECE"))
    assert [r.rule for r in result.rules] == ["cgpa"]
    assert result.verdict is Eligibility.ELIGIBLE


def test_no_stated_requirements_means_eligible():
    result = evaluate(Requirements(), Profile())
    assert result.rules == ()
    assert result.verdict is Eligibility.ELIGIBLE


def test_backlogs_allowed_means_no_backlog_rule():
    requirements = Requirements(
        min_cgpa=Decimal("7.0"), active_backlogs_allowed=True
    )
    result = evaluate(requirements, Profile(active_backlogs=3))
    assert [r.rule for r in result.rules] == ["cgpa"]
    assert result.verdict is Eligibility.ELIGIBLE
