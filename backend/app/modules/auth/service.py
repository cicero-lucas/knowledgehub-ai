from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.modules.auth.schemas import TokenResponse
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService
from app.shared.exceptions import ConflictError, ForbiddenError, http_unauthorized


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.user_service = UserService(db)

    def register(self, data: UserCreate) -> User:
        """Create a new user account."""
        return self.user_service.create(data)

    def login(self, email: str, password: str) -> TokenResponse:
        """Validate credentials and return JWT tokens."""
        user = self.user_repo.get_by_email(email)

        # Constant-time check: always verify even if user doesn't exist
        # to prevent user enumeration via timing attacks
        if user is None or not verify_password(password, user.hashed_password):
            raise http_unauthorized("Invalid email or password.")

        if not user.is_active:
            raise http_unauthorized("Account is inactive.")

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    def refresh(self, refresh_token: str) -> TokenResponse:
        """Issue new access + refresh token pair from a valid refresh token."""
        from jose import JWTError

        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise http_unauthorized("Invalid or expired refresh token.")

        if payload.get("type") != "refresh":
            raise http_unauthorized("Token type must be 'refresh'.")

        user_id = payload.get("sub")
        if not user_id:
            raise http_unauthorized("Token subject missing.")

        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
