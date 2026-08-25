"""Declarative base. Every model in app/models must import Base from here."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
