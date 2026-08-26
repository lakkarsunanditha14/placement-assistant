"""Model registry.

Alembic autogenerate only sees tables whose model classes have been imported.
Every new model must be added here, or its migration will silently not exist.
"""
from app.models.message import Message, ProcessingStatus
from app.models.source import Source, SourceKind
from app.models.student_profile import StudentProfile

__all__ = ["Message", "ProcessingStatus",
           "Source", "SourceKind", "StudentProfile"]
