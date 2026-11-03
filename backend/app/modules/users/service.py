import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate
from app.shared.exceptions import ConflictError, NotFoundError


class UserService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def get_by_id(self, user_id: uuid.UUID) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    def get_by_email(self, email: str) -> User | None:
        return self.repo.get_by_email(email)

    def create(self, data: UserCreate) -> User:
        if self.repo.email_exists(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered.")
        return self.repo.create(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )

    def update(self, user: User, data: UserUpdate) -> User:
        updates: dict = {}
        if data.full_name is not None:
            updates["full_name"] = data.full_name
        if data.email is not None and data.email != user.email:
            if self.repo.email_exists(data.email):
                raise ConflictError(f"Email '{data.email}' is already in use.")
            updates["email"] = data.email
        if not updates:
            return user
        return self.repo.update(user, **updates)

    def delete(self, user: User) -> None:
        self.repo.delete(user)

    def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> User:
        if not verify_password(current_password, user.hashed_password):
            raise ConflictError("Current password is incorrect.")
        return self.repo.update(
            user, hashed_password=hash_password(new_password)
        )
