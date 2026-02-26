from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Response
from fastapi import Depends, HTTPException, status
from fastapi.params import Cookie, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import JwtManager
from app.database import get_db
from app.exceptions.CustomExceptions import to_http_exception
from app.models import User
from app.models.Project import ProjectMember
from app.repositories.user_repository import UserRepository
from app.schemas.dto import SystemRole, ProjectRole
from app.schemas.dto import UserCreate, UserRead, Token, UserUpdate
from app.schemas.response import ResponseBase
from app.services.user.implementation import UserService

router = APIRouter(prefix="/users", tags=["Users"])

import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency factory that creates a UserService with repository for the current request."""
    service = UserService()
    service.set_repository(UserRepository(db))
    return service


def get_current_user(
        token: str = Depends(oauth2_scheme),
        user_service: UserService = Depends(get_user_service),
        db: Session = Depends(get_db),
):
    """Dependency to get the current authenticated user from JWT token."""
    try:
        payload = JwtManager.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user_id = payload.get("sub")
    user = user_service.get_user(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_system_role(*allowed_roles: SystemRole):
    """
    Dependency factory. Usage:
        Depends(require_system_role(SystemRole.ADMIN))
    """

    def guard(actor: User = Depends(get_current_user)) -> User:
        if actor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"Requires system role: "
                               f"{[r.value for r in allowed_roles]}"
                }
            )
        return actor

    return guard


def require_project_role(*allowed_roles: ProjectRole):
    """
    Dependency factory. Usage:
        Depends(require_project_role(ProjectRole.OWNER, ProjectRole.EDITOR))
    """

    def guard(
            id: int,
            actor: User = Depends(get_current_user),
            db: Session = Depends(get_db)
    ) -> User:
        # Platform admins bypass project-level checks
        if actor.role == SystemRole.admin:
            return actor

        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == id,
            ProjectMember.user_id == actor.id
        ).first()

        if not membership or membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"Requires project role: "
                               f"{[r.value for r in allowed_roles]}"
                }
            )
        return actor

    return guard


def user_access_control(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Fetch a user by ID and enforce access control.

    Rules:
    - Users can access their own profile
    - Admins can access any user
    """

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Access control rules
    if user.id == current_user.id:
        return user  # Can always access self

    if current_user.role == SystemRole.admin:
        return user  # Admin can access any user

    raise HTTPException(status_code=403, detail="Forbidden")


@router.get(
    "",
    response_model=ResponseBase[List[UserRead]],
    dependencies=[Depends(get_current_user), Depends(require_system_role(SystemRole.admin))],
    summary="List all users (admin only)",
    description=(
        "Return a paginated list of all users, with optional filtering by email and role.\n\n"
        "Requires system role `admin`."
    ),
    responses={
        200: {
            "description": "Users retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Users retrieved successfully",
                        "data": [
                            {
                                "id": 1,
                                "email": "admin@example.com",
                                "full_name": "Admin User",
                                "role": "admin",
                            }
                        ],
                    }
                }
            },
        },
        403: {
            "description": "Forbidden – caller is not an admin",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "FORBIDDEN",
                            "message": "Requires system role: ['admin']",
                        }
                    }
                }
            },
        },
    },
)
def get_all_users(
    skip: int = Query(default=0, ge=0, description="Items to skip for pagination"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of users to return"),
    email_contains: str | None = Query(default=None, description="Filter users whose email contains this value (case-insensitive)"),
    role: str | None = Query(default=None, description="Filter users by exact role (e.g. 'admin', 'member')"),
    service: UserService = Depends(get_user_service),
):
    users = service.get_all_users(skip=skip, limit=limit, email_contains=email_contains, role=role)
    user_reads = [UserRead.from_orm(u) for u in users]
    return ResponseBase(code=HTTPStatus.OK, message="Users retrieved successfully", data=user_reads)


@router.post(
    "",
    response_model=ResponseBase[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account.\n\n"
        "- Returns 201 on success.\n"
        "- Returns 400/422 for validation issues.\n"
        "- Returns 400/409 if the email is already registered."
    ),
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 201,
                        "message": "User registered successfully",
                        "data": {
                            "id": 1,
                            "email": "alice@example.com",
                            "full_name": "Alice Smith",
                            "role": "member",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Bad request / user already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with email alice@example.com already exists",
                    }
                }
            },
        },
        422: {
            "description": "Validation error (e.g. weak password, invalid email)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Password does not meet strength requirements",
                    }
                }
            },
        },
    },
)
def register_user(
        user_in: UserCreate,
        user_service: UserService = Depends(get_user_service),
) -> ResponseBase[UserRead]:
    """Register a new user.

    Raises:
        ValidationError: If input is invalid.
        PasswordTooWeak: If password is too weak.
        UserAlreadyExists: If email is already registered.
    """
    try:
        user = user_service.register(user_in)
        return ResponseBase[UserRead](code=HTTPStatus.CREATED, message="User registered successfully",
                                      data=UserRead(**user.__dict__))
    except Exception as exc:
        raise to_http_exception(exc)


@router.post(
    "/token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Obtain access token",
    description=(
        "Authenticate a user with email and password and return a JWT access token.\n\n"
        "Uses OAuth2PasswordRequestForm (application/x-www-form-urlencoded) with fields `username` and `password`."
    ),
    responses={
        200: {
            "description": "Authentication successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "<jwt-access-token>",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid username or password",
                    }
                }
            },
        },
    },
)
def login_for_access_token(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        user_service: UserService = Depends(get_user_service),
) -> Token:
    """Authenticate a user and return a JWT access token.

    Raises:
        InvalidCredentials: If email or password is incorrect.
    """
    try:
        user = user_service.authenticate(form_data.username, form_data.password)
    except Exception as exc:
        raise to_http_exception(exc)

    access_token = JwtManager.create_access_token(subject=str(user.id))
    refresh_token = JwtManager.create_refresh_token(subject=str(user.id))
    secure_cookie = os.getenv('ENV', 'development') == 'production'
    from app.core import security as core_security
    try:
        max_age = int(core_security.REFRESH_TOKEN_EXPIRE_MINUTES) * 60
    except Exception:
        max_age = None

    response.set_cookie(key="refresh",
                        value=refresh_token,
                        httponly=True,
                        secure=secure_cookie,
                        samesite="lax",
                        max_age=max_age)
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=ResponseBase[UserRead],
    summary="Get current authenticated user",
    description=(
        "Return the profile of the currently authenticated user based on the bearer access token.\n\n"
        "Requires `Authorization: Bearer <token>`."
    ),
    responses={
        200: {
            "description": "Current user profile returned",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "User profile retrieved successfully",
                        "data": {
                            "id": 1,
                            "email": "current@example.com",
                            "full_name": "Current User",
                            "role": "member",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized – missing or invalid token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid authentication credentials",
                    }
                }
            },
        },
    },
)
def read_own_user(current_user: User = Depends(get_current_user)) -> ResponseBase[UserRead]:
    """Get the current authenticated user's profile."""
    return ResponseBase(code=HTTPStatus.OK,
                        message="User profile retrieved successfully",
                        data=UserRead.from_orm(current_user))


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description=(
        "Exchange a valid refresh token (HttpOnly cookie) for a new access token.\n\n"
        "Requires `refresh` cookie containing a valid refresh JWT."
    ),
    responses={
        200: {
            "description": "New access token issued",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "<new-jwt-access-token>",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Invalid or missing refresh token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid authentication credentials",
                    }
                }
            },
        },
    },
)
def refresh_token(response: Response, refresh: str = Cookie(None)) -> Token:
    """Refresh an access token using a refresh token."""
    if not refresh:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    try:
        payload = JwtManager.decode_token(refresh)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    access_token = JwtManager.create_access_token(payload.get("sub"))
    refresh_token = JwtManager.create_refresh_token(payload.get("sub"))

    secure_cookie = os.getenv('ENV', 'development') == 'production'
    from app.core import security as core_security
    try:
        max_age = int(core_security.REFRESH_TOKEN_EXPIRE_MINUTES) * 60
    except Exception:
        max_age = None

    response.set_cookie(key="refresh",
                        value=refresh_token,
                        httponly=True,
                        secure=secure_cookie,
                        samesite="lax",
                        max_age=max_age)
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/logout",
    response_model=ResponseBase[None],
    summary="Logout current user",
    description="Clear the refresh token cookie to log the user out.",
    responses={
        200: {
            "description": "Logged out successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Logged out successfully",
                        "data": None,
                    }
                }
            },
        },
    },
)
def logout(response: Response) -> ResponseBase[None]:
    """Logout by clearing the refresh token cookie."""
    response.delete_cookie(key="refresh")
    return ResponseBase(code=HTTPStatus.OK, message="Logged out successfully", data=None)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user by id. Only admins or the user themselves (depending on access control) may delete.",
    responses={
        204: {"description": "User deleted successfully"},
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            },
        },
        403: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Forbidden"}
                }
            },
        },
    },
)
def delete_user(id: int, service: UserService = Depends(get_user_service),
                current_user: User = Depends(user_access_control)):
    """Delete a user by ID."""
    service.delete_user(id)


@router.get(
    "/{id}",
    response_model=ResponseBase[UserRead],
    dependencies=[Depends(get_current_user), Depends(user_access_control)],
    summary="Get user by id",
    description=(
        "Retrieve a specific user by id.\n\n"
        "Users can fetch their own profile; admins can fetch any user."
    ),
    responses={
        200: {
            "description": "User profile retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "User profile retrieved successfully",
                        "data": {
                            "id": 1,
                            "email": "user@example.com",
                            "full_name": "Example User",
                            "role": "member",
                        },
                    }
                }
            },
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            },
        },
        403: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Forbidden"}
                }
            },
        },
    },
)
def read_user(id: int, service: UserService = Depends(get_user_service)):
    """Get a user by ID."""
    user = service.get_user(id)
    return ResponseBase(code=HTTPStatus.OK, message="User profile retrieved successfully",
                        data=UserRead(**user.__dict__))


@router.put(
    "/{id}",
    response_model=ResponseBase[UserRead],
    dependencies=[Depends(get_current_user), Depends(user_access_control)],
    summary="Update user",
    description="Update a user's profile (full_name and/or password).",
    responses={
        200: {
            "description": "User updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "User updated successfully",
                        "data": {
                            "id": 1,
                            "email": "user@example.com",
                            "full_name": "Updated Name",
                            "role": "member",
                        },
                    }
                }
            },
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            },
        },
        403: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Forbidden"}
                }
            },
        },
    },
)
def update_user(id: int, user_in: UserUpdate, service: UserService = Depends(get_user_service)):
    """Update a user's profile (full_name and/or password)."""
    updated = service.update_user(id, **user_in.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return ResponseBase(code=HTTPStatus.OK,
                        message="User updated successfully",
                        data=UserRead.from_orm(updated))
