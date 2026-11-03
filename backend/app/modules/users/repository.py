import uuid

from sqlalchemy.orm import Session

from app.modules.users.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email_or_id(self, identifier: str) -> User | None:
        """Lookup by UUID string (from JWT sub) or email."""
        try:
            uid = uuid.UUID(identifier)
            return self.get_by_id(uid)
        except ValueError:
            return self.get_by_email(identifier)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def create(
        self,
        email: str,
        full_name: str,
        hashed_password: str,
    ) -> User:
        user = User(
            email=email.lower(),
            full_name=full_name,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, **kwargs) -> User:
        for field, value in kwargs.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()

    def email_exists(self, email: str) -> bool:
        return (
            self.db.query(User).filter(User.email == email.lower()).count() > 0
        )
