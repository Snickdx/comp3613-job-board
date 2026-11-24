from typing import Optional
from sqlmodel import Field, SQLModel

class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    graduate_id: int = Field(foreign_key="graduate.id", index=True, unique=True)
