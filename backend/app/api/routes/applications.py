"""Application endpoints, including both approval gates.

Note what is missing: there is no endpoint that sets state to PREPARING or
SUBMITTING. Those two states have exactly one door each, and the door is an
explicit approval.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Application, Opportunity
from app.models.application import ApplicationState
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStateChange,
)
from app.workflows.state_machine import (
    IllegalTransition,
    approve_preparation,
    approve_submission,
    transition,
)

router = APIRouter(prefix="/applications", tags=["applications"])

GATED_STATES = {ApplicationState.PREPARING, ApplicationState.SUBMITTING}


def _get_or_404(application_id: int, db: Session) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Application {application_id} not found."
        )
    return application


def _save(db: Session, application: Application) -> Application:
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationRead])
def list_applications(db: Session = Depends(get_db)) -> list[Application]:
    return list(
        db.execute(select(Application).order_by(
            Application.id.desc())).scalars()
    )


@router.get("/{application_id}", response_model=ApplicationRead)
def read_application(
    application_id: int, db: Session = Depends(get_db)
) -> Application:
    return _get_or_404(application_id, db)


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def start_application(
    payload: ApplicationCreate, db: Session = Depends(get_db)
) -> Application:
    """Begin tracking an opportunity.

    Walks straight to WAITING_FOR_PREPARATION_APPROVAL, because the summary
    the student needs to decide on is the opportunity row that already
    exists. It then stops, and waits — possibly forever.
    """
    if db.get(Opportunity, payload.opportunity_id) is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Opportunity {payload.opportunity_id} not found.",
        )

    application = Application(opportunity_id=payload.opportunity_id)
    db.add(application)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An application already exists for this opportunity.",
        ) from exc

    transition(application, ApplicationState.SUMMARY_READY)
    transition(application, ApplicationState.WAITING_FOR_PREPARATION_APPROVAL)
    return _save(db, application)


@router.post("/{application_id}/approve-preparation", response_model=ApplicationRead)
def gate_one(application_id: int, db: Session = Depends(get_db)) -> Application:
    """Gate 1 — explicit permission to open and fill the form."""
    application = _get_or_404(application_id, db)
    try:
        approve_preparation(application, at=datetime.now(timezone.utc))
    except IllegalTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _save(db, application)


@router.post("/{application_id}/approve-submission", response_model=ApplicationRead)
def gate_two(application_id: int, db: Session = Depends(get_db)) -> Application:
    """Gate 2 — explicit permission to submit."""
    application = _get_or_404(application_id, db)
    try:
        approve_submission(application, at=datetime.now(timezone.utc))
    except IllegalTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _save(db, application)


@router.post("/{application_id}/state", response_model=ApplicationRead)
def move_state(
    application_id: int,
    payload: ApplicationStateChange,
    db: Session = Depends(get_db),
) -> Application:
    """Move through the non-gated part of the workflow.

    Phases 12-17 replace this with the real machinery. It exists now so the
    workflow can be driven and tested end to end.
    """
    if payload.to_state in GATED_STATES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{payload.to_state.value} is reachable only through its approval "
            "endpoint. This is deliberate.",
        )

    application = _get_or_404(application_id, db)
    try:
        transition(application, payload.to_state)
    except IllegalTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _save(db, application)
