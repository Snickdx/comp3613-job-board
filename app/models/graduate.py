from typing import Optional
from sqlmodel import Field
from app.models.user import UserBase

class Graduate(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, foreign_key="user.id")
    programme: Optional[str] = None
    field_preference: Optional[str] = None
    resume_text: Optional[str] = None