from typing import Optional

from sqlmodel import Field, SQLModel


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    # Which listing the notification is about, so a subscriber is told only once (A10).
    listing_id: Optional[int] = Field(default=None, index=True)
    message: str
