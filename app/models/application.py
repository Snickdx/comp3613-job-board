from typing import Optional

from sqlmodel import Field, SQLModel


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(index=True)
    graduate_id: int = Field(index=True)
    cover_letter: str
    resume_text: str
    # Canonical label (often drifts from the boolean flags below).
    status: str
    # Poor man's lifecycle tracker: parallel flags updated ad hoc.
    flag_reviewed: int = 0
    flag_shortlisted: int = 0
    flag_rejected: int = 0
    flag_hired: int = 0
