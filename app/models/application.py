from typing import Optional
from sqlmodel import Field, SQLModel

class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.id", index=True)
    graduate_id: int = Field(foreign_key="graduate.id", index=True)
    cover_letter: str
    resume_text: str
    state: str = "submitted"

    def transition(self, action: str) -> bool:
        from app.models.states import get_state

        current_state = get_state(self.state)
        if current_state is None:
            return False
        return current_state.transition(self, action)

    def review(self) -> bool:
        return self.transition("review")

    def shortlist(self) -> bool:
        return self.transition("shortlist")

    def interview(self) -> bool:
        return self.transition("interview")

    def offer(self) -> bool:
        return self.transition("offer")

    def accept_offer(self) -> bool:
        return self.transition("accept_offer")

    def reject_offer(self) -> bool:
        return self.transition("reject_offer")

    def reject(self) -> bool:
        return self.transition("reject")

    def withdraw(self) -> bool:
        return self.transition("withdraw")

    def hire(self) -> bool:
        return self.transition("hire")