"""Trusted student profile endpoints.

This system serves exactly one student, so there is exactly one profile row.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import StudentProfile
from app.schemas.student_profile import (
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_profile(db: Session) -> StudentProfile | None:
    return db.execute(select(StudentProfile).limit(1)).scalar_one_or_none()


@router.get("", response_model=StudentProfileRead)
def read_profile(db: Session = Depends(get_db)) -> StudentProfile:
    profile = _get_profile(db)
    if profile is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "No profile has been created yet."
        )
    return profile


@router.post("", response_model=StudentProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: StudentProfileCreate, db: Session = Depends(get_db)
) -> StudentProfile:
    if _get_profile(db) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A profile already exists. Use PATCH to update it.",
        )
    profile = StudentProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("", response_model=StudentProfileRead)
def update_profile(
    payload: StudentProfileUpdate, db: Session = Depends(get_db)
) -> StudentProfile:
    profile = _get_profile(db)
    if profile is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "No profile has been created yet."
        )

    # exclude_unset is the important part: a field the caller did not send is
    # left untouched, not overwritten with null. Erasing a verified fact
    # because it was absent from a request would be a form of guessing.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
