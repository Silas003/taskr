from fastapi import HTTPException

class EntityNotFound(Exception):
    def __init__(self, entity_name: str, entity_id: int):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with id {entity_id} not found")

class UnauthorizedAccess(Exception):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message)

class ValidationError(Exception):
    def __init__(self, message: str ):
        self.message = message
        super().__init__(message)

class DatabaseError(Exception):
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message)

class BadRequest(Exception):
    def __init__(self, message: str ):
        self.message = message
        super().__init__(message)

class ServerError(Exception):
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message)

# User-workflow specific exceptions
class UserAlreadyExists(BadRequest):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists")
        self.email = email

class InvalidCredentials(UnauthorizedAccess):
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)

class PasswordTooWeak(ValidationError):
    def __init__(self, message: str = "Password does not meet strength requirements"):
        super().__init__(message)

def to_http_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, UserAlreadyExists):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, InvalidCredentials):
        return HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, PasswordTooWeak) or isinstance(exc, ValidationError) or isinstance(exc, BadRequest):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, EntityNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, UnauthorizedAccess):
        return HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, DatabaseError):
        return HTTPException(status_code=500, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))
