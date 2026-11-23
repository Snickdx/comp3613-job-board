"""State pattern for the application lifecycle.

One state object per status. Each action either returns the name of the next
status or raises InvalidTransitionError. Rejected and Hired are final.

Legal moves:
    submitted   -> reviewed
    reviewed    -> shortlisted | rejected
    shortlisted -> hired | rejected
"""

from __future__ import annotations


class InvalidTransitionError(Exception):
    """Raised when an action is not allowed from the current status."""


class ApplicationState:
    name: str = ""

    def _invalid(self, action: str) -> str:
        raise InvalidTransitionError(f"cannot {action} an application that is {self.name}")

    def transition(self, action: str) -> str:
        return self._invalid(action)

    def review(self) -> str:
        return self._invalid("review")

    def shortlist(self) -> str:
        return self._invalid("shortlist")

    def reject(self) -> str:
        return self._invalid("reject")

    def hire(self) -> str:
        return self._invalid("hire")

    def _refuse(self, action: str) -> str:
        return self._invalid(action)


class SubmittedState(ApplicationState):
    name = "submitted"

    def transition(self, action: str) -> str:
        if action == "mark_reviewed":
            return "reviewed"
        return self._invalid(action)

    def review(self) -> str:
        return ReviewedState.name


class ReviewedState(ApplicationState):
    name = "reviewed"

    def transition(self, action: str) -> str:
        if action == "shortlist":
            return "shortlisted"
        if action == "reject":
            return "rejected"
        return self._invalid(action)

    def shortlist(self) -> str:
        return ShortlistedState.name

    def reject(self) -> str:
        return RejectedState.name


class ShortlistedState(ApplicationState):
    name = "shortlisted"

    def transition(self, action: str) -> str:
        if action == "hire":
            return "hired"
        if action == "reject":
            return "rejected"
        return self._invalid(action)

    def hire(self) -> str:
        return HiredState.name

    def reject(self) -> str:
        return RejectedState.name


class RejectedState(ApplicationState):
    """Final state: every action is refused."""

    name = "rejected"


class HiredState(ApplicationState):
    """Final state: every action is refused."""

    name = "hired"


class ApplicationStateFactory:
    _states = {
        state.name: state
        for state in (
            SubmittedState,
            ReviewedState,
            ShortlistedState,
            RejectedState,
            HiredState,
        )
    }

    @classmethod
    def create(cls, status: str) -> ApplicationState:
        try:
            return cls._states[status]()
        except KeyError:
            raise InvalidTransitionError(f"unknown status {status!r}") from None

    @classmethod
    def from_status(cls, status: str) -> ApplicationState:
        return cls.create(status)
