from fastapi import APIRouter, status

from app.core.database import DbSession
from app.modules.auth.dependencies import CurrentUser
from app.modules.users.schemas import UserResponse, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse, summary="Update current user profile")
def update_me(
    data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    service = UserService(db)
    updated_user = service.update(current_user, data)
    return UserResponse.model_validate(updated_user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account",
)
def delete_me(current_user: CurrentUser, db: DbSession) -> None:
    service = UserService(db)
    service.delete(current_user)
