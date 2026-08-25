"""In-memory source adapter for tests and local development.

Satisfies the same contract as the real Telegram adapter will in Phase 4, so
any pipeline built against this keeps working unchanged when the real source
arrives.

The fixtures deliberately cover the content types from section 9 of the guide:
job, hackathon, announcement, test/interview, shortlist, irrelevant and
ambiguous. Later phases get judged on whether they route all of these
correctly — including the ones that must NOT become applications.
"""
from datetime import datetime, timezone

from app.services.ingestion.base import (
    RawAttachment,
    RawMessage,
    SourceAdapter,
    SourceMetadata,
)


def _at(day: int, hour: int = 10, minute: int = 0) -> datetime:
    """Fixed timestamps. No clock reads — fixtures must be identical on
    every run, or tests become flaky for reasons unrelated to the code."""
    return datetime(2026, 8, day, hour, minute, tzinfo=timezone.utc)


DEFAULT_MESSAGES: list[RawMessage] = [
    # A real job posting. Everything the extractor needs is present.
    RawMessage(
        external_id="m-001",
        posted_at=_at(20, 9, 30),
        author_display_name="Placement Cell",
        text=(
            "ABC Technologies — Software Engineer (2027 batch)\n"
            "CTC: 8 LPA\n"
            "Eligibility: CSE / IT, minimum 7.0 CGPA, no active backlogs\n"
            "Skills: Python, SQL, Machine Learning\n"
            "Apply: https://careers.abctech.example/apply/se-2027\n"
            "Last date: 28 August 2026, 5:00 PM\n"
            "Service agreement: 2 years"
        ),
    ),
    # A hackathon. Must never be treated as a job application.
    RawMessage(
        external_id="m-002",
        posted_at=_at(21, 11, 0),
        author_display_name="Placement Cell",
        text=(
            "HackVerse 2026 registrations are open. Teams of 3-4. "
            "Open to all branches and years. "
            "Register by 30 August: https://hackverse.example/register"
        ),
    ),
    # An announcement. Store and notify, no application.
    RawMessage(
        external_id="m-003",
        posted_at=_at(21, 16, 15),
        author_display_name="Placement Cell",
        text=(
            "Reminder: placement policy briefing tomorrow at 11:00 AM in the "
            "seminar hall. Attendance is compulsory for all final year students."
        ),
    ),
    # A test/interview call. Date, time and instructions to extract.
    RawMessage(
        external_id="m-004",
        posted_at=_at(22, 10, 0),
        author_display_name="Placement Cell",
        text=(
            "ABC Technologies online assessment on 30 August 2026 at 10:00 AM. "
            "Duration 90 minutes. The link will be shared 30 minutes prior. "
            "Keep your college ID ready."
        ),
    ),
    # A shortlist with a PDF. Phase 9 must understand the document's purpose
    # BEFORE it looks for the student's name in it.
    RawMessage(
        external_id="m-005",
        posted_at=_at(23, 14, 45),
        author_display_name="Placement Cell",
        text=(
            "Shortlisted candidates for ABC Technologies Round 2 are listed in "
            "the attached PDF. Please check your roll number."
        ),
        attachment_ids=("a-001",),
    ),
    # Irrelevant. No placement action of any kind.
    RawMessage(
        external_id="m-006",
        posted_at=_at(23, 18, 0),
        author_display_name="Hostel Office",
        text="The canteen will remain closed on Saturday due to maintenance.",
    ),
    # Ambiguous on purpose. No company, no link, no deadline date.
    # The correct behaviour is to ask or flag — never to guess.
    RawMessage(
        external_id="m-007",
        posted_at=_at(24, 9, 0),
        author_display_name="Placement Cell",
        text="Interested students please fill the form by tomorrow.",
    ),
]

DEFAULT_ATTACHMENTS: dict[str, list[RawAttachment]] = {
    "m-005": [
        RawAttachment(
            external_id="a-001",
            filename="abc_technologies_round2_shortlist.pdf",
            media_type="application/pdf",
            size_bytes=48_213,
        )
    ]
}


class MockSourceAdapter(SourceAdapter):
    """A source that lives entirely in memory."""

    def __init__(
        self,
        external_id: str = "mock-placement-group",
        display_name: str = "Mock Placement Group",
        messages: list[RawMessage] | None = None,
        attachments: dict[str, list[RawAttachment]] | None = None,
    ) -> None:
        self._external_id = external_id
        self._display_name = display_name
        self._messages = list(
            DEFAULT_MESSAGES if messages is None else messages)
        self._attachments = dict(
            DEFAULT_ATTACHMENTS if attachments is None else attachments
        )

    def get_source_metadata(self) -> SourceMetadata:
        return SourceMetadata(
            kind="mock",
            external_id=self._external_id,
            display_name=self._display_name,
        )

    def read_messages(
        self, since: datetime | None = None, limit: int = 100
    ) -> list[RawMessage]:
        messages = sorted(self._messages, key=lambda m: m.posted_at)
        if since is not None:
            messages = [m for m in messages if m.posted_at > since]
        return messages[:limit]

    def read_permitted_attachments(
        self, message_external_id: str
    ) -> list[RawAttachment]:
        return list(self._attachments.get(message_external_id, []))
