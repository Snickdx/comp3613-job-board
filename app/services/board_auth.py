"""Scenario auth helpers (email login + public user dicts)."""

from __future__ import annotations
from typing import Any
from sqlmodel import Session, select
from app.database import engine
from app.models.user import User
from app.models.admin import Admin
from app.models.employer import Employer
from app.models.graduate import Graduate
from app.utilities.security import verify_password


def public_user(
    user: User | dict | None,
    session: Session | None = None,
) -> dict[str, Any] | None:

    if user is None:
        return None
    
    if isinstance(user, dict):
        data = dict(user)
    else:
        data = user.model_dump()
    data.pop("password", None)
    data.pop("password_hash", None)
    if session is not None and not isinstance(user, dict):
        if session.get(Admin, user.id) is not None:
            data["role"] = "admin"
        elif session.get(Graduate, user.id) is not None:
            data["role"] = "graduate"
        elif session.get(Employer, user.id) is not None:
            data["role"] = "employer"

    return data


def login(email: str, password: str) -> dict[str, Any] | None:

    with Session(engine) as session:

        user = session.exec(
            select(User).where(User.email == email)
        ).one_or_none()

        if user is None or not verify_password(password, user.password):
            return None
        
        return public_user(user, session)


def get_user(user_id: int) -> dict[str, Any] | None:

    with Session(engine) as session:

        user = session.get(User, user_id)
        
        return public_user(user, session)
