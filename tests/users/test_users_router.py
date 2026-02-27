"""
Tests for the users API router (app/routers/users.py)

Uses FastAPI's TestClient with dependency overrides so no real DB or JWT
calls are made.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routers.v1.users import (
    router,
    get_user_service,
    get_current_user,
    user_access_control,
)
from app.models.User import User
from app.schemas.dto import SystemRole
from app.exceptions.CustomExceptions import UserAlreadyExists, InvalidCredentials


# ---------------------------------------------------------------------------
# App / Client setup
# ---------------------------------------------------------------------------

app = FastAPI()
app.include_router(router)


def _make_user(
    id=1,
    email="alice@example.com",
    full_name="Alice Smith",
    role=SystemRole.member,
):
    u = User()
    u.id = id
    u.email = email
    u.full_name = full_name
    u.password = "hashed"
    u.role = role
    u.created_at = datetime(2024, 1, 1)
    u.updated_at = datetime(2024, 1, 2)
    return u


ALICE = _make_user()
ADMIN = _make_user(id=2, email="admin@example.com", role=SystemRole.admin)


def _override_service(user=None, users=None, deleted=True):
    svc = MagicMock()
    svc.register.return_value = user or ALICE
    svc.authenticate.return_value = user or ALICE
    svc.get_user.return_value = user or ALICE
    svc.get_all_users.return_value = users or [ALICE]
    svc.update_user.return_value = user or ALICE
    svc.delete_user.return_value = deleted
    return svc


@pytest.fixture
def client_as_alice():
    svc = _override_service()
    app.dependency_overrides[get_user_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[user_access_control] = lambda: ALICE
    yield TestClient(app), svc
    app.dependency_overrides.clear()


@pytest.fixture
def client_as_admin():
    svc = _override_service(users=[ALICE, ADMIN])
    app.dependency_overrides[get_user_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    app.dependency_overrides[user_access_control] = lambda: ADMIN
    yield TestClient(app), svc
    app.dependency_overrides.clear()


@pytest.fixture
def client_unauthenticated():
    svc = _override_service()
    app.dependency_overrides[get_user_service] = lambda: svc
    yield TestClient(app), svc
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /users  – register
# ---------------------------------------------------------------------------
class TestRegisterUser:
    def test_register_success(self, client_unauthenticated):
        client, svc = client_unauthenticated
        payload = {
            "email": "alice@example.com",
            "password": "StrongPass1!",
            "full_name": "Alice Smith",
        }
        resp = client.post("/users", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["email"] == "alice@example.com"

    def test_register_duplicate_email_returns_400(self, client_unauthenticated):
        client, svc = client_unauthenticated
        svc.register.side_effect = UserAlreadyExists("alice@example.com")
        payload = {"email": "alice@example.com", "password": "StrongPass1!"}
        resp = client.post("/users", json=payload)
        assert resp.status_code == 400

    def test_register_invalid_email_returns_422(self, client_unauthenticated):
        client, _ = client_unauthenticated
        resp = client.post("/users", json={"email": "not-an-email", "password": "StrongPass1!"})
        assert resp.status_code == 422

    def test_register_short_password_returns_422(self, client_unauthenticated):
        client, _ = client_unauthenticated
        resp = client.post("/users", json={"email": "bob@example.com", "password": "short"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /users/token  – login
# ---------------------------------------------------------------------------
class TestLogin:
    def test_login_success_returns_token(self, client_unauthenticated):
        client, svc = client_unauthenticated
        with patch("app.routers.v1.users.JwtManager") as mock_jwt:
            mock_jwt.create_access_token.return_value = "access_tok"
            mock_jwt.create_refresh_token.return_value = "refresh_tok"
            resp = client.post(
                "/users/token",
                data={"username": "alice@example.com", "password": "StrongPass1!"},
            )
        assert resp.status_code == 200
        assert resp.json()["access_token"] == "access_tok"
        assert resp.json()["token_type"] == "bearer"

    def test_login_sets_refresh_cookie(self, client_unauthenticated):
        client, svc = client_unauthenticated
        with patch("app.routers.v1.users.JwtManager") as mock_jwt:
            mock_jwt.create_access_token.return_value = "access_tok"
            mock_jwt.create_refresh_token.return_value = "refresh_tok"
            resp = client.post(
                "/users/token",
                data={"username": "alice@example.com", "password": "StrongPass1!"},
            )
        assert "refresh" in resp.cookies

    def test_login_invalid_credentials_returns_401(self, client_unauthenticated):
        client, svc = client_unauthenticated
        svc.authenticate.side_effect = InvalidCredentials()
        resp = client.post(
            "/users/token",
            data={"username": "alice@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------
class TestReadOwnUser:
    def test_returns_current_user(self, client_as_alice):
        client, _ = client_as_alice
        resp = client.get("/users/me")
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "alice@example.com"


# ---------------------------------------------------------------------------
# POST /users/refresh
# ---------------------------------------------------------------------------
class TestRefreshToken:
    def test_refresh_success(self, client_unauthenticated):
        client, _ = client_unauthenticated
        with patch("app.routers.v1.users.JwtManager") as mock_jwt:
            mock_jwt.decode_token.return_value = {"sub": "1", "type": "refresh"}
            mock_jwt.create_access_token.return_value = "new_access"
            mock_jwt.create_refresh_token.return_value = "new_refresh"
            client.cookies.set("refresh", "valid_refresh_token")
            resp = client.post("/users/refresh")
        assert resp.status_code == 200
        assert resp.json()["access_token"] == "new_access"

    def test_refresh_without_cookie_returns_401(self, client_unauthenticated):
        client, _ = client_unauthenticated
        resp = client.post("/users/refresh")
        assert resp.status_code == 401

    def test_refresh_with_invalid_token_returns_401(self, client_unauthenticated):
        client, _ = client_unauthenticated
        with patch("app.routers.v1.users.JwtManager") as mock_jwt:
            mock_jwt.decode_token.side_effect = ValueError("bad token")
            client.cookies.set("refresh", "invalid")
            resp = client.post("/users/refresh")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/logout
# ---------------------------------------------------------------------------
class TestLogout:
    def test_logout_clears_cookie(self, client_as_alice):
        client, _ = client_as_alice
        resp = client.get("/users/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"


# ---------------------------------------------------------------------------
# GET /users  – list all (admin only)
# ---------------------------------------------------------------------------
class TestGetAllUsers:
    def test_admin_can_list_users(self, client_as_admin):
        client, svc = client_as_admin
        resp = client.get("/users")
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_pagination_params_forwarded(self, client_as_admin):
        client, svc = client_as_admin
        client.get("/users?skip=5&limit=20")
        svc.get_all_users.assert_called_once_with(skip=5, limit=20)

    def test_invalid_limit_returns_422(self, client_as_admin):
        client, _ = client_as_admin
        resp = client.get("/users?limit=0")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------
class TestReadUser:
    def test_returns_user_by_id(self, client_as_alice):
        client, svc = client_as_alice
        resp = client.get("/users/1")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == 1

    def test_service_called_with_correct_id(self, client_as_alice):
        client, svc = client_as_alice
        client.get("/users/1")
        svc.get_user.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# PUT /users/{id}
# ---------------------------------------------------------------------------
class TestUpdateUser:
    def test_update_full_name(self, client_as_alice):
        client, svc = client_as_alice
        resp = client.put("/users/1", json={"full_name": "Alice Updated"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "User updated successfully"

    def test_update_returns_404_when_not_found(self, client_as_alice):
        client, svc = client_as_alice
        svc.update_user.return_value = None
        resp = client.put("/users/1", json={"full_name": "Ghost"})
        assert resp.status_code == 404

    def test_update_excludes_unset_fields(self, client_as_alice):
        client, svc = client_as_alice
        client.put("/users/1", json={"full_name": "New Name"})
        call_kwargs = svc.update_user.call_args
        # password should NOT be in kwargs since it was not sent
        assert "password" not in call_kwargs.kwargs or call_kwargs.kwargs.get("password") is None


# ---------------------------------------------------------------------------
# DELETE /users/{id}
# ---------------------------------------------------------------------------
class TestDeleteUser:
    def test_delete_returns_204(self, client_as_alice):
        client, svc = client_as_alice
        resp = client.delete("/users/1")
        assert resp.status_code == 204

    def test_service_called_with_correct_id(self, client_as_alice):
        client, svc = client_as_alice
        client.delete("/users/1")
        svc.delete_user.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# Dependency: get_current_user
# ---------------------------------------------------------------------------
class TestGetCurrentUserDependency:
    def test_invalid_token_raises_401(self):
        """Test that invalid token raises 401 via the real dependency."""
        test_app = FastAPI()
        test_app.include_router(router)
        c = TestClient(test_app, raise_server_exceptions=False)
        resp = c.get("/users/me", headers={"Authorization": "Bearer bad_token"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Dependency: user_access_control
# ---------------------------------------------------------------------------
class TestUserAccessControl:
    def test_user_can_access_own_profile(self):
        from app.routers.v1.users import user_access_control
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = ALICE
        result = user_access_control(user_id=1, db=db, current_user=ALICE)
        assert result is ALICE

    def test_admin_can_access_any_user(self):
        from app.routers.v1.users import user_access_control
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = ALICE
        result = user_access_control(user_id=1, db=db, current_user=ADMIN)
        assert result is ALICE

    def test_other_user_raises_403(self):
        from fastapi import HTTPException
        from app.routers.v1.users import user_access_control
        other = _make_user(id=3, email="other@example.com")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = other
        with pytest.raises(HTTPException) as exc_info:
            user_access_control(user_id=3, db=db, current_user=ALICE)
        assert exc_info.value.status_code == 403

    def test_user_not_found_raises_404(self):
        from fastapi import HTTPException
        from app.routers.v1.users import user_access_control
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            user_access_control(user_id=99, db=db, current_user=ALICE)
        assert exc_info.value.status_code == 404
