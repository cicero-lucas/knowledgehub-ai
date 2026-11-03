from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.database import DbSession
from app.core.security import decode_token
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.shared.exceptions import http_unauthorized

http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(http_bearer)
    ] = None,
) -> User:
    """
    FastAPI dependency: extracts and validates the Bearer JWT,
    returns the active User or raises 401.
    """
    if credentials is None:
        raise http_unauthorized("Authorization header missing.")

    token = credentials.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise http_unauthorized("Invalid or expired token.")

    if payload.get("type") != "access":
        raise http_unauthorized("Token type must be 'access'.")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise http_unauthorized("Token subject missing.")

    user = UserRepository(db).get_by_email_or_id(user_id)
    if user is None:
        raise http_unauthorized("User not found.")

    if not user.is_active:
        raise http_unauthorized("Account is inactive.")

    return user


# Typed alias for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
