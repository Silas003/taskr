from abc import ABC, abstractmethod
from typing import Optional

from app.models.User import User
from app.schemas.dto import UserCreate


class IUserService(ABC):
    """Abstract interface for user service operations."""

    @abstractmethod
    def register(self, user_in: UserCreate) -> User:
        """Register a new user."""
        pass

    @abstractmethod
    def authenticate(self, email: str, password: str) -> User:
        """Authenticate a user."""
        pass

    @abstractmethod
    def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        pass

    @abstractmethod
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        pass

    @abstractmethod
    def get_all_users(self, limit: int, offset: int):
        """Retrieve all users."""
        pass
