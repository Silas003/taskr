import re
from app.exceptions.CustomExceptions import PasswordTooWeak, ValidationError


def validate_password_strength(password: str) -> None:
    """Raise PasswordTooWeak if password doesn't meet basic strength rules.

    Rules (example):
    - minimum 8 characters
    - at least one uppercase, one lowercase, one digit
    - optionally, at least one special character
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
    # optional: special char
    # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
    #     raise PasswordTooWeak("Password must contain at least one special character")


def validate_email_format(email: str) -> None:
    # Basic check — use pydantic EmailStr in schemas for stronger validation
    if not email or "@" not in email:
        raise ValidationError("Invalid email address")

