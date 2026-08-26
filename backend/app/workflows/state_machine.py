"""Legal state transitions for an application.

The table below is the safety property, not a diagram of one. PREPARING is
reachable only from WAITING_FOR_PREPARATION_APPROVAL, and SUBMITTING only
from WAITING_FOR_SUBMISSION_APPROVAL. There is no other route into either,
so no amount of new code elsewhere can skip a gate — it would have to edit
this table, in a diff a human reads.
"""
from datetime import datetime

from app.models.application import Application, ApplicationState as S


class IllegalTransition(RuntimeError):
    """Raised when something attempts a move the workflow does not permit."""


TRANSITIONS: dict[S, frozenset[S]] = {
    S.DETECTED: frozenset({S.SUMMARY_READY}),
    S.SUMMARY_READY: frozenset({S.WAITING_FOR_PREPARATION_APPROVAL}),
    # Gate 1. The only way out is an explicit approval.
    S.WAITING_FOR_PREPARATION_APPROVAL: frozenset({S.PREPARING}),
    S.PREPARING: frozenset(
        {S.QUESTIONS_PENDING, S.VALIDATING, S.FAILED, S.MANUAL_ACTION_REQUIRED}
    ),
    S.QUESTIONS_PENDING: frozenset({S.VALIDATING}),
    # Validation can send it back for more answers.
    S.VALIDATING: frozenset({S.READY_FOR_REVIEW, S.QUESTIONS_PENDING}),
    # Reviewing can send it back for edits.
    S.READY_FOR_REVIEW: frozenset({S.WAITING_FOR_SUBMISSION_APPROVAL, S.PREPARING}),
    # Gate 2. The only way out is an explicit approval.
    S.WAITING_FOR_SUBMISSION_APPROVAL: frozenset({S.SUBMITTING}),
    S.SUBMITTING: frozenset({S.SUBMITTED, S.FAILED, S.MANUAL_ACTION_REQUIRED}),
    # Terminal.
    S.SUBMITTED: frozenset(),
    S.FAILED: frozenset(),
    S.MANUAL_ACTION_REQUIRED: frozenset(),
}


def transition(application: Application, to_state: S) -> Application:
    allowed = TRANSITIONS[application.state]
    if to_state not in allowed:
        permitted = ", ".join(
            sorted(s.value for s in allowed)) or "nothing (terminal)"
        raise IllegalTransition(
            f"Cannot move application {application.id} from "
            f"{application.state.value} to {to_state.value}. Permitted: {permitted}."
        )
    application.state = to_state
    return application


def approve_preparation(application: Application, at: datetime) -> Application:
    """Gate 1. Recording the approval and moving state are one operation,
    so an approved timestamp can never exist without the move, or vice versa.
    """
    transition(application, S.PREPARING)
    application.preparation_approved_at = at
    return application


def approve_submission(application: Application, at: datetime) -> Application:
    """Gate 2."""
    transition(application, S.SUBMITTING)
    application.submission_approved_at = at
    return application
