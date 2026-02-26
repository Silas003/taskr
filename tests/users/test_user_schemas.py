"""
Tests for User Pydantic schemas (app/schemas/User.py)
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.dto import (
    UserCreate,
    UserUpdate,
    UserRead,
    Token,
    ProjectRead,
    TaskBase,
    TaskStatusEnum,
    SystemRole
)


# ---------------------------------------------------------------------------
# UserCreate
# ---------------------------------------------------------------------------
class TestUserCreate:
    def test_valid_minimal(self):
        u = UserCreate(email="bob@example.com", password="12345678")
        assert u.email == "bob@example.com"
        assert u.full_name is None
        assert u.role == SystemRole.member

    def test_valid_full(self):
        u = UserCreate(
            email="bob@example.com",
            password="StrongPass1!",
            full_name="Bob Jones",
            role=SystemRole.admin,
        )
        assert u.full_name == "Bob Jones"
        assert u.role == SystemRole.admin

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="12345678")

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="bob@example.com", password="short")

    def test_password_exactly_8_chars_valid(self):
        u = UserCreate(email="bob@example.com", password="exactly8")
        assert len(u.password) == 8

    def test_default_role_is_member(self):
        u = UserCreate(email="bob@example.com", password="12345678")
        assert u.role == SystemRole.member


# ---------------------------------------------------------------------------
# UserUpdate
# ---------------------------------------------------------------------------
class TestUserUpdate:
    def test_all_fields_optional(self):
        u = UserUpdate()
        assert u.full_name is None
        assert u.password is None

    def test_valid_with_full_name(self):
        u = UserUpdate(full_name="New Name")
        assert u.full_name == "New Name"

    def test_valid_with_password(self):
        u = UserUpdate(password="NewPass123!")
        assert u.password == "NewPass123!"

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            UserUpdate(password="short")

    def test_dict_exclude_unset(self):
        u = UserUpdate(full_name="Only Name")
        d = u.dict(exclude_unset=True)
        assert "full_name" in d
        assert "password" not in d


# ---------------------------------------------------------------------------
# UserRead
# ---------------------------------------------------------------------------
class TestUserRead:
    def _make_orm_user(self):
        from types import SimpleNamespace
        return SimpleNamespace(
            id=1,
            email="alice@example.com",
            full_name="Alice",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2),
            role=SystemRole.member,
        )

    def test_from_orm(self):
        orm_user = self._make_orm_user()
        r = UserRead.from_orm(orm_user)
        assert r.id == 1
        assert r.email == "alice@example.com"
        assert r.role == SystemRole.member

    def test_direct_construction(self):
        r = UserRead(
            id=1,
            email="alice@example.com",
            full_name="Alice",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2),
            role=SystemRole.member,
        )
        assert r.id == 1

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            UserRead(email="alice@example.com")  # missing id, timestamps, role


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------
class TestToken:
    def test_default_token_type(self):
        t = Token(access_token="abc123")
        assert t.token_type == "bearer"

    def test_custom_token_type(self):
        t = Token(access_token="abc", token_type="jwt")
        assert t.token_type == "jwt"

    def test_missing_access_token_raises(self):
        with pytest.raises(ValidationError):
            Token()


# ---------------------------------------------------------------------------
# TaskStatusEnum
# ---------------------------------------------------------------------------
class TestTaskStatusEnum:
    def test_values(self):
        assert TaskStatusEnum.pending == "pending"
        assert TaskStatusEnum.in_progress == "in_progress"
        assert TaskStatusEnum.completed == "completed"

    def test_is_str(self):
        assert isinstance(TaskStatusEnum.pending, str)


# ---------------------------------------------------------------------------
# ProjectRead
# ---------------------------------------------------------------------------
class TestProjectRead:
    def test_valid_construction(self):
        p = ProjectRead(
            id=1,
            name="My Project",
            description="A description",
            owner_id=5,
            created_at=datetime(2024, 3, 1),
        )
        assert p.name == "My Project"
        assert p.owner_id == 5

    def test_optional_description(self):
        p = ProjectRead(
            id=1, name="P", description=None, owner_id=1, created_at=datetime.now()
        )
        assert p.description is None


# ---------------------------------------------------------------------------
# TaskBase
# ---------------------------------------------------------------------------
class TestTaskBase:
    def test_valid_construction(self):
        t = TaskBase(
            id=1,
            title="Fix bug",
            description="Something is broken",
            project_id=2,
            status=TaskStatusEnum.pending,
            due_date=None,
            created_at=datetime(2024, 1, 1),
        )
        assert t.title == "Fix bug"
        assert t.status == TaskStatusEnum.pending

    def test_optional_description_and_due_date(self):
        t = TaskBase(
            id=1,
            title="Task",
            description=None,
            project_id=1,
            status=TaskStatusEnum.completed,
            due_date=None,
            created_at=datetime.now(),
        )
        assert t.description is None
        assert t.due_date is None

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            TaskBase(
                id=1,
                title="Task",
                project_id=1,
                status="invalid_status",
                created_at=datetime.now(),
            )
