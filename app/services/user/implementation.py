from typing import Optional, List

from app.exceptions.CustomExceptions import UserAlreadyExists, InvalidCredentials
from app.models.User import User
from app.repositories.user_repository import IUserRepository
from app.schemas.User import UserCreate
from app.security.password_manager import PasswordManager
from app.services.user.interfaces import IUserService
from app.validators.user_validator import UserValidator


class UserService(IUserService):
    """Service layer for user-related operations."""



    def __init__(
            self,
            repository: Optional[IUserRepository] = None,
            password_manager: Optional[PasswordManager] = None,
            validator: Optional[UserValidator] = None,
    ):
        """Initialize the user service with dependencies.

        Args:
            repository: User repository implementation. Defaults to None (will be set per request).
            password_manager: Password manager instance. Defaults to a new PasswordManager().
            validator: User validator instance. Defaults to UserValidator.
        """
        self.repository = repository
        self.password_manager = password_manager or PasswordManager()
        self.validator = validator or UserValidator()

    def set_repository(self, repository: IUserRepository) -> None:
        """Set the repository (for dependency injection per request)."""
        self.repository = repository

    def register(self, user_in: UserCreate) -> User:
        """Register a new user.

        Args:
            user_in: User creation schema.

        Returns:
            Created User instance.

        Raises:
            ValidationError: If input validation fails.
            PasswordTooWeak: If password does not meet strength requirements.
            UserAlreadyExists: If email is already registered.
        """

        # Validate inputs
        self.validator.validate_email_format(str(user_in.email))
        self.validator.validate_password_strength(user_in.password)
        if user_in.full_name:
            self.validator.validate_full_name(user_in.full_name)

        # Check if user already exists
        existing = self.repository.get_by_email(str(user_in.email))
        if existing:
            raise UserAlreadyExists(str(user_in.email))

        # Hash password and create user
        hashed_password = self.password_manager.hash_password(user_in.password)
        user = User(
            email=str(user_in.email),
            full_name=user_in.full_name,
            password=hashed_password,
        )
        return self.repository.save(user)

    def authenticate(self, email: str, password: str) -> User:
        """Authenticate a user by email and password.

        Args:
            email: User email address.
            password: User password (plaintext).

        Returns:
            Authenticated User instance.

        Raises:
            InvalidCredentials: If email/password combination is invalid.
        """

        user = self.repository.get_by_email(email)
        if not user:
            raise InvalidCredentials()

        if not self.password_manager.verify_password(password, user.password):
            raise InvalidCredentials()

        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID.

        Args:
            user_id: User ID.

        Returns:
            User instance or None if not found.
        """

        return self.repository.get_by_id(user_id)

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields.

        Args:
            user_id: User ID.
            **kwargs: Fields to update (e.g., full_name, password).

        Returns:
            Updated User instance or None if not found.

        Raises:
            ValidationError: If updated data is invalid.
        """

        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        # Validate and update fields
        if "full_name" in kwargs and kwargs["full_name"]:
            self.validator.validate_full_name(kwargs["full_name"])
            user.full_name = kwargs["full_name"]

        if "password" in kwargs and kwargs["password"]:
            self.validator.validate_password_strength(kwargs["password"])
            user.password = self.password_manager.hash_password(kwargs["password"])

        return self.repository.update(user)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID.

        Args:
            user_id: User ID.

        Returns:
            True if deleted, False if not found.
        """
        return self.repository.delete(user_id)

    def get_all_users(self, limit: int, offset: int):
        self.repository.find_all(limit, offset)