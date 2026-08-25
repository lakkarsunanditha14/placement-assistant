"""Authorized placement source endpoints.

Register, authorize, revoke, read. That is the complete list.

There is no endpoint here — and there will never be one — that sends,
replies, posts, reacts, edits, deletes or forwards through a source.
Read-only is not a setting on this system; it is the absence of any code
that could do otherwise.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Source
from app.schemas.source import SourceCreate, SourceRead

router = APIRouter(prefix="/sources", tags=["sources"])


def _get_or_404(source_id: int, db: Session) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Source {source_id} not found."
        )
    return source


@router.get("", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)) -> list[Source]:
    return list(db.execute(select(Source).order_by(Source.id)).scalars())


@router.get("/{source_id}", response_model=SourceRead)
def read_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    return _get_or_404(source_id, db)


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def register_source(
    payload: SourceCreate, db: Session = Depends(get_db)
) -> Source:
    """Register a source. It is NOT authorized by this call."""
    source = Source(**payload.model_dump())  # authorized stays False
    db.add(source)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This source is already registered.",
        )
    db.refresh(source)
    return source


@router.post("/{source_id}/authorize", response_model=SourceRead)
def authorize_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    """Explicit authorization. This is the only way a source becomes readable."""
    source = _get_or_404(source_id, db)
    source.authorized = True
    source.authorized_at = datetime.now(timezone.utc)
    source.revoked_at = None
    db.commit()
    db.refresh(source)
    return source


@router.post("/{source_id}/revoke", response_model=SourceRead)
def revoke_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    """Withdraw authorization. Takes effect immediately for all readers."""
    source = _get_or_404(source_id, db)
    source.authorized = False
    source.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(source)
    return source
