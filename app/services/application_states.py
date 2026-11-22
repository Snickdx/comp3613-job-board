from __future__ import annotations


class IllegalTransition(Exception):
    def __init__(self, status: str, action: str) -> None:
        self.status = status
        self.action = action
        super().__init__(f"cannot {action} an application in status {status}")


class ApplicationState:
    status = ""

    def review(self) -> "ApplicationState":
        raise IllegalTransition(self.status, "review")

    def mark_reviewed(self) -> "ApplicationState":
        raise IllegalTransition(self.status, "mark_reviewed")

    def shortlist(self) -> "ApplicationState":
        raise IllegalTransition(self.status, "shortlist")

    def reject(self) -> "ApplicationState":
        raise IllegalTransition(self.status, "reject")

    def hire(self) -> "ApplicationState":
        raise IllegalTransition(self.status, "hire")

    def reopen(self) -> "ApplicationState":
        raise IllegalTransition(self.status, "reopen")

    def transition(self, action: str) -> "ApplicationState":
        actions = {
            "review": self.review,
            "mark_reviewed": self.mark_reviewed,
            "shortlist": self.shortlist,
            "reject": self.reject,
            "hire": self.hire,
            "reopen": self.reopen,
        }
        handler = actions.get(action)
        if handler is None:
            raise ValueError(f"unknown action {action!r}")
        return handler()


class SubmittedState(ApplicationState):
    status = "submitted"

    def review(self) -> "ReviewedState":
        return ReviewedState()

    def mark_reviewed(self) -> "ReviewedState":
        return ReviewedState()


class ReviewedState(ApplicationState):
    status = "reviewed"

    def shortlist(self) -> "ShortlistedState":
        return ShortlistedState()

    def reject(self) -> "RejectedState":
        return RejectedState()


class ShortlistedState(ApplicationState):
    status = "shortlisted"

    def hire(self) -> "HiredState":
        return HiredState()

    def reject(self) -> "RejectedState":
        return RejectedState()


class RejectedState(ApplicationState):
    status = "rejected"

    def reopen(self) -> "ReviewedState":
        return ReviewedState()


class HiredState(ApplicationState):
    status = "hired"


STATES: dict[str, ApplicationState] = {
    "submitted": SubmittedState(),
    "reviewed": ReviewedState(),
    "shortlisted": ShortlistedState(),
    "rejected": RejectedState(),
    "hired": HiredState(),
}


def state_for(status: str) -> ApplicationState:
    try:
        return STATES[status]
    except KeyError as exc:
        raise ValueError(f"unknown application status {status!r}") from exc
