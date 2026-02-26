from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session
from app.models.User import User


class IUserRepository(ABC):
    """Abstract base class defining the user repository contract."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Add a new user to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update an existing user."""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        pass

    @abstractmethod
    def find_all(self, limit: int, offset: int):
        """Retrieve all users with pagination."""
        pass


class UserRepository(IUserRepository):
    """SQLAlchemy-based implementation of IUserRepository."""

    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def find_all(self, limit: int, offset: int):
        return self.db.query(User).offset(offset).limit(limit).all()
