from typing import Optional

from sqlmodel import Field, SQLModel


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(index=True)
    graduate_id: int = Field(index=True)
    cover_letter: str
    resume_text: str
    # Canonical lifecycle status: the single source of truth.
    status: str
    # Legacy flags, kept for database compatibility. lifecycle.py derives
    # them from `status` on every change, so they cannot drift.
    flag_reviewed: int = 0
    flag_shortlisted: int = 0
    flag_rejected: int = 0
    flag_hired: int = 0
