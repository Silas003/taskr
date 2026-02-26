"""
Tests for UserService (app/services/user/implementation.py)
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.user.implementation import UserService
from app.models.User import User
from app.exceptions.CustomExceptions import UserAlreadyExists, InvalidCredentials
from app.schemas.dto import SystemRole,UserCreate


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_password_manager():
    pm = MagicMock()
    pm.hash_password.return_value = "hashed_pw"
    pm.verify_password.return_value = True
    return pm


@pytest.fixture
def mock_validator():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_password_manager, mock_validator):
    svc = UserService(
        repository=mock_repo,
        password_manager=mock_password_manager,
        validator=mock_validator,
    )
    return svc


@pytest.fixture
def user_create():
    return UserCreate(
        email="alice@example.com",
        password="StrongPass1!",
        full_name="Alice Smith",
        role=SystemRole.member,
    )


@pytest.fixture
def sample_user():
    user = User()
    user.id = 1
    user.email = "alice@example.com"
    user.full_name = "Alice Smith"
    user.password = "hashed_pw"
    user.role = SystemRole.member
    return user


# ---------------------------------------------------------------------------
# __init__ / set_repository
# ---------------------------------------------------------------------------
class TestInit:
    def test_defaults_are_set(self):
        svc = UserService()
        assert svc.repository is None
        assert svc.password_manager is not None
        assert svc.validator is not None

    def test_set_repository(self, service, mock_repo):
        new_repo = MagicMock()
        service.set_repository(new_repo)
        assert service.repository is new_repo


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------
class TestRegister:
    def test_register_success(self, service, mock_repo, mock_validator, mock_password_manager, user_create, sample_user):
        mock_repo.get_by_email.return_value = None
        mock_repo.save.return_value = sample_user

        result = service.register(user_create)

        mock_validator.validate_email_format.assert_called_once_with(str(user_create.email))
        mock_validator.validate_password_strength.assert_called_once_with(user_create.password)
        mock_validator.validate_full_name.assert_called_once_with(user_create.full_name)
        mock_password_manager.hash_password.assert_called_once_with(user_create.password)
        mock_repo.save.assert_called_once()
        assert result is sample_user

    def test_register_raises_when_email_exists(self, service, mock_repo, user_create, sample_user):
        mock_repo.get_by_email.return_value = sample_user

        with pytest.raises(UserAlreadyExists):
            service.register(user_create)

        mock_repo.save.assert_not_called()

    def test_register_without_full_name_skips_name_validation(self, service, mock_repo, mock_validator, sample_user):
        user_in = UserCreate(email="bob@example.com", password="StrongPass1!")
        mock_repo.get_by_email.return_value = None
        mock_repo.save.return_value = sample_user

        service.register(user_in)
        mock_validator.validate_full_name.assert_not_called()

    def test_register_hashes_password_before_saving(self, service, mock_repo, mock_password_manager, user_create, sample_user):
        mock_repo.get_by_email.return_value = None
        mock_repo.save.return_value = sample_user

        service.register(user_create)

        saved_user: User = mock_repo.save.call_args[0][0]
        assert saved_user.password == "hashed_pw"

    def test_register_calls_email_check_with_string(self, service, mock_repo, user_create, sample_user):
        """Ensures email is cast to str before repository lookup."""
        mock_repo.get_by_email.return_value = None
        mock_repo.save.return_value = sample_user
        service.register(user_create)
        mock_repo.get_by_email.assert_called_once_with(str(user_create.email))


# ---------------------------------------------------------------------------
# authenticate()
# ---------------------------------------------------------------------------
class TestAuthenticate:
    def test_authenticate_success(self, service, mock_repo, mock_password_manager, sample_user):
        mock_repo.get_by_email.return_value = sample_user
        mock_password_manager.verify_password.return_value = True

        result = service.authenticate("alice@example.com", "StrongPass1!")
        assert result is sample_user

    def test_authenticate_raises_when_user_not_found(self, service, mock_repo):
        mock_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentials):
            service.authenticate("ghost@example.com", "anything")

    def test_authenticate_raises_when_password_wrong(self, service, mock_repo, mock_password_manager, sample_user):
        mock_repo.get_by_email.return_value = sample_user
        mock_password_manager.verify_password.return_value = False

        with pytest.raises(InvalidCredentials):
            service.authenticate("alice@example.com", "wrongpassword")


# ---------------------------------------------------------------------------
# get_user()
# ---------------------------------------------------------------------------
class TestGetUser:
    def test_returns_user_when_found(self, service, mock_repo, sample_user):
        mock_repo.get_by_id.return_value = sample_user
        result = service.get_user(1)
        mock_repo.get_by_id.assert_called_once_with(1)
        assert result is sample_user

    def test_returns_none_when_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        result = service.get_user(999)
        assert result is None


# ---------------------------------------------------------------------------
# update_user()
# ---------------------------------------------------------------------------
class TestUpdateUser:
    def test_update_full_name(self, service, mock_repo, mock_validator, sample_user):
        mock_repo.get_by_id.return_value = sample_user
        mock_repo.update.return_value = sample_user

        result = service.update_user(1, full_name="New Name")

        mock_validator.validate_full_name.assert_called_once_with("New Name")
        assert sample_user.full_name == "New Name"
        assert result is sample_user

    def test_update_password(self, service, mock_repo, mock_validator, mock_password_manager, sample_user):
        mock_repo.get_by_id.return_value = sample_user
        mock_repo.update.return_value = sample_user

        service.update_user(1, password="NewStrongPass1!")

        mock_validator.validate_password_strength.assert_called_once_with("NewStrongPass1!")
        mock_password_manager.hash_password.assert_called_once_with("NewStrongPass1!")
        assert sample_user.password == "hashed_pw"

    def test_update_returns_none_when_user_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        result = service.update_user(999, full_name="Ghost")
        assert result is None
        mock_repo.update.assert_not_called()

    def test_update_skips_validation_for_empty_full_name(self, service, mock_repo, mock_validator, sample_user):
        mock_repo.get_by_id.return_value = sample_user
        mock_repo.update.return_value = sample_user

        service.update_user(1, full_name=None)
        mock_validator.validate_full_name.assert_not_called()

    def test_update_skips_password_hash_for_none_password(self, service, mock_repo, mock_password_manager, sample_user):
        mock_repo.get_by_id.return_value = sample_user
        mock_repo.update.return_value = sample_user

        service.update_user(1, password=None)
        mock_password_manager.hash_password.assert_not_called()


# ---------------------------------------------------------------------------
# delete_user()
# ---------------------------------------------------------------------------
class TestDeleteUser:
    def test_delete_returns_true(self, service, mock_repo):
        mock_repo.delete.return_value = True
        result = service.delete_user(1)
        mock_repo.delete.assert_called_once_with(1)
        assert result is True

    def test_delete_returns_false_when_not_found(self, service, mock_repo):
        mock_repo.delete.return_value = False
        result = service.delete_user(999)
        assert result is False


# ---------------------------------------------------------------------------
# get_all_users()
# ---------------------------------------------------------------------------
class TestGetAllUsers:
    def test_returns_paginated_users(self, service, mock_repo, sample_user):
        mock_repo.find_all.return_value = [sample_user]
        result = service.get_all_users(skip=0, limit=10)
        mock_repo.find_all.assert_called_once_with(limit=10, offset=0)
        assert result == [sample_user]

    def test_returns_empty_list(self, service, mock_repo):
        mock_repo.find_all.return_value = []
        result = service.get_all_users(skip=0, limit=10)
        assert result == []

    def test_passes_skip_as_offset(self, service, mock_repo):
        mock_repo.find_all.return_value = []
        service.get_all_users(skip=20, limit=5)
        mock_repo.find_all.assert_called_once_with(limit=5, offset=20)
