"""Application lifecycle implementation using the State design pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

ACTIONS = (
    "mark_reviewed",
    "shortlist",
    "reject",
    "hire",
    "reopen",
)


class ApplicationState(ABC):
    @property
    @abstractmethod
    def status(self) -> str:
        """Return the state's canonical status name."""

    @abstractmethod
    def transition(self, action: str) -> "ApplicationState | None":
        """Return the next state for a legal action, or None."""


class SubmittedState(ApplicationState):
    @property
    def status(self) -> str:
        return "submitted"

    def transition(self, action: str) -> "ApplicationState | None":
        if action == "mark_reviewed":
            return ReviewedState()
        return None


class ReviewedState(ApplicationState):
    @property
    def status(self) -> str:
        return "reviewed"

    def transition(self, action: str) -> "ApplicationState | None":
        if action == "shortlist":
            return ShortlistedState()
        if action == "reject":
            return RejectedState()
        return None


class ShortlistedState(ApplicationState):
    @property
    def status(self) -> str:
        return "shortlisted"

    def transition(self, action: str) -> "ApplicationState | None":
        if action == "reject":
            return RejectedState()
        if action == "hire":
            return HiredState()
        return None


class RejectedState(ApplicationState):
    @property
    def status(self) -> str:
        return "rejected"

    def transition(self, action: str) -> "ApplicationState | None":
        if action == "reopen":
            return SubmittedState()
        return None


class HiredState(ApplicationState):
    @property
    def status(self) -> str:
        return "hired"

    def transition(self, action: str) -> "ApplicationState | None":
        return None


STATE_TYPES: dict[str, type[ApplicationState]] = {
    "submitted": SubmittedState,
    "reviewed": ReviewedState,
    "shortlisted": ShortlistedState,
    "rejected": RejectedState,
    "hired": HiredState,
}


def state_for(status: str) -> ApplicationState:
    try:
        state_type = STATE_TYPES[status]
    except KeyError:
        raise ValueError(f"unknown application status {status!r}") from None
    return state_type()


def snapshot(app: dict[str, Any]) -> dict[str, Any]:
    result = {"id": app["id"], "status": app["status"]}
    for flag in (
        "flag_reviewed",
        "flag_shortlisted",
        "flag_rejected",
        "flag_hired",
    ):
        if flag in app:
            result[flag] = bool(app[flag])
    return result


def apply_action(app: dict[str, Any], action: str) -> dict[str, Any]:
    if action not in ACTIONS:
        return {
            "ok": False,
            "error": f"unknown action {action!r}; expected one of {ACTIONS}",
        }

    if "status" not in app:
        return {"ok": False, "error": "application status is missing"}

    try:
        current_state = state_for(app["status"])
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    next_state = current_state.transition(action)
    if next_state is None:
        return {
            "ok": False,
            "error": f"cannot {action} application in {current_state.status} state",
        }

    updated = dict(app)
    updated["status"] = next_state.status
    return {"ok": True, "application": snapshot(updated), "row": updated, "changed": True}


def derived_status_from_flags(app: dict[str, Any]) -> str:
    """Compatibility helper; Application.status is the source of truth."""
    return app["status"]
