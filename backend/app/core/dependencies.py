from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        token_role = payload.get("role")
        if not isinstance(user_id, str) or not isinstance(token_role, str):
            raise _credentials_exception()
    except (JWTError, TypeError, ValueError):
        raise _credentials_exception() from None

    user = get_user_by_id(db, user_id)
    if user is None or user.role != token_role:
        raise _credentials_exception()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str) -> Callable:
    allowed = frozenset(role.upper() for role in allowed_roles)

    def dependency(current_user: CurrentUser) -> User:
        if current_user.role.upper() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


def require_authenticated_user(current_user: CurrentUser) -> User:
    return current_user


def require_doctor(current_user: CurrentUser) -> User:
    return require_roles("DOCTOR")(current_user)


def require_doctor_or_student(current_user: CurrentUser) -> User:
    return require_roles("DOCTOR", "STUDENT")(current_user)


__all__ = [
    "CurrentUser",
    "get_current_user",
    "oauth2_scheme",
    "require_authenticated_user",
    "require_doctor",
    "require_doctor_or_student",
    "require_roles",
]
