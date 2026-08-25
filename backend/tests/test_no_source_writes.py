"""Mandatory safety test — no source write operation exists.

This test reads the application's own route table. If someone later adds an
endpoint that could write to a placement source, this fails immediately,
before the code can ever run against a real Telegram group.
"""
from app.main import app

# The complete, deliberate list of things this system may do to a source.
ALLOWED_SOURCE_OPERATIONS = {
    "list_sources",
    "read_source",
    "register_source",
    "authorize_source",
    "revoke_source",
}

FORBIDDEN_WORDS = ("send", "reply", "react", "forward", "broadcast", "publish")


def test_sources_expose_only_allowlisted_operations():
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/sources"):
            continue

        name = getattr(route, "name", "")
        assert name in ALLOWED_SOURCE_OPERATIONS, (
            f"New operation '{name}' found on {path}. Placement sources are "
            "read-only. Adding an operation here must be a deliberate, "
            "reviewed decision — update the allowlist only if it truly reads."
        )


def test_source_routes_never_use_destructive_http_methods():
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/sources"):
            continue

        methods = getattr(route, "methods", set()) or set()
        assert methods <= {"GET", "POST"}, (
            f"{path} exposes {methods - {'GET', 'POST'}}, which implies "
            "modifying a source."
        )


def test_no_route_anywhere_is_named_after_a_write_action():
    for route in app.routes:
        name = (getattr(route, "name", "") or "").lower()
        for word in FORBIDDEN_WORDS:
            assert word not in name, (
                f"Route '{name}' suggests writing to a source. "
                "This system never sends, replies, reacts or forwards."
            )
