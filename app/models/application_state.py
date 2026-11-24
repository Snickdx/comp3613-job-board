from abc import ABC
from typing import ClassVar


class ApplicationState(ABC):
    allowed_actions: ClassVar[frozenset[str]] = frozenset()

    def transition(self, application, action: str) -> bool:
        if action not in self.allowed_actions:
            return False
        method = getattr(self, action, None)
        if not callable(method):
            return False
        previous_state = application.state
        method(application)
        return application.state != previous_state