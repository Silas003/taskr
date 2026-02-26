import re
from app.exceptions.CustomExceptions import PasswordTooWeak, ValidationError


class UserValidator:
    """Validates user input for registration and updates."""

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """Validate password strength against requirements.

        Rules:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if not password:
            raise ValidationError("Password is required")
        if len(password) < 8:
            raise PasswordTooWeak("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise PasswordTooWeak("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise PasswordTooWeak("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", password):
            raise PasswordTooWeak("Password must contain at least one digit")

    @staticmethod
    def validate_email_format(email: str) -> None:
        """Validate basic email format.

        Note: EmailStr in Pydantic schemas provides stronger validation.
        This is a secondary check.
        """
        if not email or "@" not in email:
            raise ValidationError("Invalid email address")
        if len(email) > 255:
            raise ValidationError("Email address is too long")

    @staticmethod
    def validate_full_name(full_name: str) -> None:
        """Validate full name is not empty and within reasonable bounds."""
        if full_name and len(full_name) > 255:
            raise ValidationError("Full name is too long")

