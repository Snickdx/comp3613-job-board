from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
import jwt
from jwt.exceptions import InvalidTokenError
from app.config import get_settings
from app.models.user import User
from app.dependencies.session import SessionDep
from app.repositories.user import UserRepository
from app.models.admin import Admin

async def get_current_user(request:Request, db:SessionDep)->User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("access_token")
    if token is None:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id = payload.get("sub", None)
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except (InvalidTokenError, ValueError, TypeError) as e:
        print("Invalid token error: ", e)
        raise credentials_exception

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception
    
    return user


async def is_logged_in(
    request: Request,
    db:SessionDep
) -> bool:
    
    try:
        await get_current_user(request, db)
        return True
    except HTTPException:
        return False


IsUserLoggedIn = Annotated[bool, Depends(is_logged_in)]
AuthDep = Annotated[User, Depends(get_current_user)]


async def is_admin(
    user: User,
    db: SessionDep
) -> bool:
    
    admin = db.get(Admin, user.id)

    return admin is not None


async def is_admin_dep(
    user: AuthDep,
    db: SessionDep
) -> Admin:

    admin = db.get(Admin, user.id)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this page",
        )
    
    return admin


AdminDep = Annotated[Admin, Depends(is_admin_dep)]
