from typing import Optional
from sqlmodel import Field
from app.models.user import UserBase
    
class Admin(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, foreign_key="user.id")
