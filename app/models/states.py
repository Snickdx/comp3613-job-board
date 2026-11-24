from app.models.application_state import ApplicationState


class AppliedState(ApplicationState):
    allowed_actions = frozenset({"review"})

    def review(self, application):
        application.state = "reviewed"


class ReviewedState(ApplicationState):
    allowed_actions = frozenset({"shortlist"})

    def shortlist(self, application):
        application.state = "shortlisted"


class ShortlistedState(ApplicationState):
    allowed_actions = frozenset({"reject", "hire"})

    def reject(self, application):
        application.state = "rejected"

    def hire(self, application):
        application.state = "hired"


class InterviewState(ApplicationState):
    pass


class OfferedState(ApplicationState):
    pass


class HiredState(ApplicationState):
    pass


class RejectedState(ApplicationState):
    pass


class WithdrawnState(ApplicationState):
    pass


SubmittedState = AppliedState


STATE_CLASSES = {
    "submitted": AppliedState,
    "reviewed": ReviewedState,
    "shortlisted": ShortlistedState,
    "hired": HiredState,
    "rejected": RejectedState,
}


def get_state(status: str) -> ApplicationState | None:
    state_class = STATE_CLASSES.get(status)
    if state_class is None:
        return None
    return state_class()