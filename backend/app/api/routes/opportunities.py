"""Opportunity endpoints, including the deterministic eligibility check."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Opportunity, StudentProfile
from app.schemas.opportunity import (
    EligibilityRead,
    OpportunityCreate,
    OpportunityRead,
    RuleResultRead,
)
from app.services.eligibility.evaluator import Requirements, evaluate

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _get_or_404(opportunity_id: int, db: Session) -> Opportunity:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Opportunity {opportunity_id} not found."
        )
    return opportunity


def _requirements_of(opportunity: Opportunity) -> Requirements:
    """Translate stored columns into the evaluator's input.

    The evaluator knows nothing about the database, which is what lets it
    be tested with plain values.
    """
    return Requirements(
        branches=tuple(opportunity.eligible_branches)
        if opportunity.eligible_branches
        else None,
        min_cgpa=opportunity.min_cgpa,
        graduation_year=opportunity.eligible_graduation_year,
        active_backlogs_allowed=opportunity.active_backlogs_allowed,
    )


@router.get("", response_model=list[OpportunityRead])
def list_opportunities(db: Session = Depends(get_db)) -> list[Opportunity]:
    return list(
        db.execute(select(Opportunity).order_by(
            Opportunity.id.desc())).scalars()
    )


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def read_opportunity(
    opportunity_id: int, db: Session = Depends(get_db)
) -> Opportunity:
    return _get_or_404(opportunity_id, db)


@router.post(
    "", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED
)
def create_opportunity(
    payload: OpportunityCreate, db: Session = Depends(get_db)
) -> Opportunity:
    opportunity = Opportunity(**payload.model_dump())
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.get("/{opportunity_id}/eligibility", response_model=EligibilityRead)
def check_eligibility(
    opportunity_id: int, db: Session = Depends(get_db)
) -> EligibilityRead:
    """Evaluate this opportunity against the trusted profile.

    Computed on demand rather than stored. The inputs are both in the
    database, so the answer is reproducible at any time.
    ponytail: not persisted; add an EligibilityResult table if the audit
    log needs to show what the verdict was at a past moment.
    """
    opportunity = _get_or_404(opportunity_id, db)

    profile = db.execute(select(StudentProfile).limit(1)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No student profile exists. Eligibility cannot be decided without one.",
        )

    result = evaluate(_requirements_of(opportunity), profile)

    return EligibilityRead(
        opportunity_id=opportunity.id,
        verdict=result.verdict.value,
        rules=[
            RuleResultRead(
                rule=r.rule, outcome=r.outcome.value, explanation=r.explanation
            )
            for r in result.rules
        ],
    )
