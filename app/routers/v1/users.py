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

router = APIRouter(prefix="/users", tags=["users"])

import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


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


@router.get("", response_model=ResponseBase[List[UserRead]],
            dependencies=[Depends(get_current_user), Depends(require_system_role(SystemRole.admin))])
def get_all_users(skip: int = Query(default=0, ge=0),
                  limit: int = Query(default=10, ge=1, le=100),
                  service: UserService = Depends(get_user_service)):
    users = service.get_all_users(skip=skip, limit=limit)
    # Pydantic can turn list of ORM users into list of UserRead
    user_reads = [UserRead.from_orm(u) for u in users]
    return ResponseBase(code=HTTPStatus.OK,
                        message="Users retrieved successfully",
                        data=user_reads)


@router.post("", response_model=ResponseBase[UserRead], status_code=status.HTTP_201_CREATED)
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


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
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
    # set cookie expiry explicitly in seconds (based on core settings default)
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


@router.get("/me", response_model=ResponseBase[UserRead])
def read_own_user(current_user: User = Depends(get_current_user)) -> ResponseBase[UserRead]:
    """Get the current authenticated user's profile."""
    return ResponseBase(code=HTTPStatus.OK,
                        message="User profile retrieved successfully",
                        data=UserRead.from_orm(current_user))


@router.post("/refresh", response_model=Token)
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


@router.get("/logout", response_model=ResponseBase[None])
def logout(response: Response) -> ResponseBase[None]:
    """Logout by clearing the refresh token cookie."""
    response.delete_cookie(key="refresh")
    return ResponseBase(code=HTTPStatus.OK, message="Logged out successfully", data=None)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, service: UserService = Depends(get_user_service),
                current_user: User = Depends(user_access_control)):
    """Delete a user by ID."""
    service.delete_user(id)


@router.get("/{id}", response_model=ResponseBase[UserRead],
            dependencies=[Depends(get_current_user), Depends(user_access_control)])
def read_user(id: int, service: UserService = Depends(get_user_service)):
    """Get a user by ID."""
    user = service.get_user(id)
    return ResponseBase(code=HTTPStatus.OK, message="User profile retrieved successfully",
                        data=UserRead(**user.__dict__))


@router.put("/{id}", response_model=ResponseBase[UserRead],
            dependencies=[Depends(get_current_user), Depends(user_access_control)])
def update_user(id: int, user_in: UserUpdate, service: UserService = Depends(get_user_service)):
    """Update a user's profile (full_name and/or password)."""
    updated = service.update_user(id, **user_in.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return ResponseBase(code=HTTPStatus.OK,
                        message="User updated successfully",
                        data=UserRead.from_orm(updated))
