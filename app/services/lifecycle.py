"""
Application lifecycle: submitted -> reviewed -> shortlisted -> rejected | hired.

Refactored to the State pattern (see app/services/application_states.py).
The `status` string is the single source of truth. The four legacy flag
columns are kept for the database schema but are now derived from the status
on every change, so they can no longer drift out of sync.
"""

from __future__ import annotations

from typing import Any

from app.services.application_states import (
    ApplicationStateFactory,
    InvalidTransitionError,
)

ACTIONS = ("mark_reviewed", "shortlist", "reject", "hire")


def apply_action(app: Any, action: str) -> dict[str, Any]:
    """Apply a valid action, or return an HTTP-mappable transition error."""
    if action not in ACTIONS:
        return {
            "ok": False,
            "code": "invalid_transition",
            "error": f"cannot {action} an application that is {getattr(app, 'status', 'unknown')}",
        }

    current_status = getattr(app, "status", "unknown")
    try:
        state = ApplicationStateFactory.create(current_status)
        new_status = state.transition(action)
    except InvalidTransitionError as exc:
        return {"ok": False, "code": "invalid_transition", "error": str(exc)}

    app.status = new_status
    app.flag_reviewed = int(new_status != "submitted")
    app.flag_shortlisted = int(new_status in {"shortlisted", "hired"})
    app.flag_rejected = int(new_status == "rejected")
    app.flag_hired = int(new_status == "hired")
    return {
        "ok": True,
        "application": app.model_dump(),
        "changed": True,
    }
