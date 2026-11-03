from fastapi import APIRouter, status

from app.core.database import DbSession
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(data: UserCreate, db: DbSession) -> UserResponse:
    service = AuthService(db)
    user = service.register(data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse, summary="Login and get JWT tokens")
def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    return service.login(data.email, data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
def refresh(data: RefreshRequest, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    return service.refresh(data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (client-side token invalidation)",
)
def logout(_: CurrentUser) -> MessageResponse:
    # JWT is stateless: the client discards the token.
    # For full server-side revocation, a token blacklist (Redis) can be added.
    return MessageResponse(message="Logged out successfully.")
