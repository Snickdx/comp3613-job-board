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

    def _refuse(self, action: str) -> str:
        raise InvalidTransitionError(
            f"cannot {action} an application that is {self.name}"
        )

    def review(self) -> str:
        return self._refuse("review")

    def shortlist(self) -> str:
        return self._refuse("shortlist")

    def reject(self) -> str:
        return self._refuse("reject")

    def hire(self) -> str:
        return self._refuse("hire")


class SubmittedState(ApplicationState):
    name = "submitted"

    def review(self) -> str:
        return ReviewedState.name


class ReviewedState(ApplicationState):
    name = "reviewed"

    def shortlist(self) -> str:
        return ShortlistedState.name

    def reject(self) -> str:
        return RejectedState.name


class ShortlistedState(ApplicationState):
    name = "shortlisted"

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
    def from_status(cls, status: str) -> ApplicationState:
        try:
            return cls._states[status]()
        except KeyError:
            raise InvalidTransitionError(f"unknown status {status!r}") from None
