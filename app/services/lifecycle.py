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

# Actions employers may attempt from the API.
ACTIONS = (
    "mark_reviewed",
    "shortlist",
    "reject",
    "hire",
    "reopen",  # always refused: rejected and hired are final
)

_ACTION_TO_METHOD = {
    "mark_reviewed": "review",
    "shortlist": "shortlist",
    "reject": "reject",
    "hire": "hire",
}


def snapshot(app: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": app["id"],
        "status": app["status"],
        "flag_reviewed": bool(app["flag_reviewed"]),
        "flag_shortlisted": bool(app["flag_shortlisted"]),
        "flag_rejected": bool(app["flag_rejected"]),
        "flag_hired": bool(app["flag_hired"]),
    }


def _flags_for(app: dict[str, Any], new_status: str) -> dict[str, int]:
    """Derive the legacy flags from the new status."""
    return {
        "flag_reviewed": 0 if new_status == "submitted" else 1,
        "flag_shortlisted": 1
        if new_status in ("shortlisted", "hired")
        else int(app["flag_shortlisted"]),
        "flag_rejected": 1 if new_status == "rejected" else 0,
        "flag_hired": 1 if new_status == "hired" else 0,
    }


def apply_action(app: dict[str, Any], action: str) -> dict[str, Any]:
    """
    Apply an action to an application row.

    Returns {"ok": True, "application", "row", "changed": True} on success.
    Returns {"ok": False, "error", "code"} when refused; the application is
    left unchanged. code is "unknown_action" or "invalid_transition".
    """
    if action not in ACTIONS:
        return {
            "ok": False,
            "code": "unknown_action",
            "error": f"unknown action {action!r}; expected one of {ACTIONS}",
        }

    try:
        state = ApplicationStateFactory.from_status(app["status"])
        if action == "reopen":
            raise InvalidTransitionError(
                f"cannot reopen an application that is {state.name}"
            )
        new_status = getattr(state, _ACTION_TO_METHOD[action])()
    except InvalidTransitionError as exc:
        return {"ok": False, "code": "invalid_transition", "error": str(exc)}

    updated = dict(app)
    updated["status"] = new_status
    updated.update(_flags_for(app, new_status))
    return {
        "ok": True,
        "application": snapshot(updated),
        "row": updated,
        "changed": True,
    }


def derived_status_from_flags(app: dict[str, Any]) -> str:
    """Kept for compatibility. Now always agrees with `status`."""
    if app["flag_hired"]:
        return "hired"
    if app["flag_rejected"]:
        return "rejected"
    if app["flag_shortlisted"]:
        return "shortlisted"
    if app["flag_reviewed"]:
        return "reviewed"
    return "submitted"
