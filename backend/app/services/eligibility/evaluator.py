"""Deterministic eligibility evaluation.

No AI here, ever. Claude's job (Phase 6) is to extract what a message *says*
the requirements are. This module's job is to decide whether the student
meets them. Mixing the two would make an eligibility answer unexplainable
and unrepeatable — 8.1 >= 7.0 is arithmetic, not interpretation.

Every rule returns its own outcome and a sentence explaining it, so the
verdict can always be shown as reasoning rather than asserted.
"""
import enum
from dataclasses import dataclass
from decimal import Decimal


class RuleOutcome(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class Eligibility(str, enum.Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class Requirements:
    """What the opportunity demands. None means the message didn't say."""

    branches: tuple[str, ...] | None = None
    min_cgpa: Decimal | None = None
    graduation_year: int | None = None
    active_backlogs_allowed: bool | None = None


@dataclass(frozen=True)
class RuleResult:
    rule: str
    outcome: RuleOutcome
    explanation: str


@dataclass(frozen=True)
class EligibilityResult:
    verdict: Eligibility
    rules: tuple[RuleResult, ...]


def _branch_rule(required: tuple[str, ...], branch: str | None) -> RuleResult:
    allowed = ", ".join(required)
    if branch is None:
        return RuleResult(
            "branch", RuleOutcome.UNKNOWN, f"Branch not in profile; requires {allowed}"
        )
    if branch.casefold() in {b.casefold() for b in required}:
        return RuleResult("branch", RuleOutcome.PASS, f"Branch {branch} is in {allowed}")
    return RuleResult("branch", RuleOutcome.FAIL, f"Branch {branch} is not in {allowed}")


def _cgpa_rule(required: Decimal, cgpa: Decimal | None) -> RuleResult:
    if cgpa is None:
        return RuleResult(
            "cgpa", RuleOutcome.UNKNOWN, f"CGPA not in profile; requires {required}"
        )
    if cgpa >= required:
        return RuleResult("cgpa", RuleOutcome.PASS, f"CGPA {cgpa} >= required {required}")
    return RuleResult("cgpa", RuleOutcome.FAIL, f"CGPA {cgpa} < required {required}")


def _graduation_year_rule(required: int, year: int | None) -> RuleResult:
    if year is None:
        return RuleResult(
            "graduation_year",
            RuleOutcome.UNKNOWN,
            f"Graduation year not in profile; requires {required}",
        )
    if year == required:
        return RuleResult(
            "graduation_year",
            RuleOutcome.PASS,
            f"Graduation year {year} matches {required}",
        )
    return RuleResult(
        "graduation_year", RuleOutcome.FAIL, f"Graduation year {year} is not {required}"
    )


def _backlog_rule(backlogs: int | None) -> RuleResult:
    """Only called when the opportunity disallows active backlogs."""
    if backlogs is None:
        return RuleResult(
            "active_backlogs",
            RuleOutcome.UNKNOWN,
            "Backlog count not in profile; no active backlogs permitted",
        )
    if backlogs == 0:
        return RuleResult(
            "active_backlogs", RuleOutcome.PASS, "No active backlogs, as required"
        )
    return RuleResult(
        "active_backlogs",
        RuleOutcome.FAIL,
        f"{backlogs} active backlog(s); none permitted",
    )


def evaluate(requirements: Requirements, profile) -> EligibilityResult:
    """Compare requirements against a trusted profile.

    `profile` is anything carrying branch, cgpa, graduation_year and
    active_backlogs — a StudentProfile row, or a stub in a test.

    A requirement the message never stated is not a rule. A profile field
    the student never gave is UNKNOWN, never assumed.
    """
    rules: list[RuleResult] = []

    if requirements.branches:
        rules.append(_branch_rule(requirements.branches, profile.branch))

    if requirements.min_cgpa is not None:
        rules.append(_cgpa_rule(requirements.min_cgpa, profile.cgpa))

    if requirements.graduation_year is not None:
        rules.append(
            _graduation_year_rule(
                requirements.graduation_year, profile.graduation_year)
        )

    if requirements.active_backlogs_allowed is False:
        rules.append(_backlog_rule(profile.active_backlogs))

    outcomes = {rule.outcome for rule in rules}
    if RuleOutcome.FAIL in outcomes:
        verdict = Eligibility.NOT_ELIGIBLE
    elif RuleOutcome.UNKNOWN in outcomes:
        verdict = Eligibility.NEEDS_REVIEW
    else:
        verdict = Eligibility.ELIGIBLE

    return EligibilityResult(verdict=verdict, rules=tuple(rules))
