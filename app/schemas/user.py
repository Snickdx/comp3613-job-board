from app.models.user import UserBase
from sqlmodel import SQLModel
from pydantic import EmailStr
from typing import Optional


class UserUpdate(SQLModel):
    username: Optional[str]
    email: Optional[EmailStr]
 
class AdminCreate(UserBase):
    pass

class GraduateCreate(UserBase):
    pass

class UserResponse(SQLModel):
    id: int
    username:str
    email: EmailStr

class SignupRequest(SQLModel):
    username: str
    email: EmailStr
    password: str
