"""Application lifecycle transitions using the State pattern."""

from __future__ import annotations

from typing import Any

from app.services.application_states import IllegalTransition, state_for

ACTIONS = (
    "review",
    "mark_reviewed",
    "shortlist",
    "reject",
    "hire",
    "reopen",
)


def apply_action(app: dict[str, Any], action: str) -> dict[str, Any]:
    if action not in ACTIONS:
        return {
            "ok": False,
            "code": "invalid_action",
            "error": f"unknown action {action!r}; expected one of {ACTIONS}",
        }

    try:
        next_state = state_for(app["status"]).transition(action)
    except IllegalTransition as exc:
        return {"ok": False, "code": "illegal_transition", "error": str(exc)}
    except ValueError as exc:
        return {"ok": False, "code": "invalid_action", "error": str(exc)}

    updated = dict(app)
    updated["status"] = next_state.status
    return {
        "ok": True,
        "application": dict(updated),
        "row": updated,
        "changed": updated["status"] != app["status"],
    }
