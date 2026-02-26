# conftest.py – shared fixtures for the test suite
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models.User import User
from app.schemas.UserSchema import SystemRole
from app.security.password_manager import PasswordManager


# ---------------------------------------------------------------------------
# Database – one in-memory SQLite engine per test session, fresh schema per test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    """Create a single SQLite in-memory engine reused across the whole session."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture
def db(engine) -> Session:
    """
    Provide a transactional database session that is rolled back after each test,
    keeping tests fully isolated without recreating the schema every time.
    """
    connection = engine.connect()
    transaction = connection.begin()
    TestingSession = sessionmaker(bind=connection)
    session = TestingSession()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# FastAPI app with DB override
# ---------------------------------------------------------------------------

@pytest.fixture
def app(db):
    """Return the FastAPI app with get_db overridden to use the test session."""
    from app.main import app as fastapi_app  # adjust import path if needed

    fastapi_app.dependency_overrides[get_db] = lambda: db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app) -> TestClient:
    """HTTP test client wired to the test database."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Reusable model factories
# ---------------------------------------------------------------------------

@pytest.fixture
def password_manager():
    return PasswordManager()


@pytest.fixture
def make_user(db, password_manager):
    """
    Factory fixture: call make_user(...) to insert a real User row and return it.

    Usage:
        def test_something(make_user):
            user = make_user(email="bob@example.com", password="StrongPass1!")
    """
    def _make_user(
        email: str = "test@example.com",
        password: str = "StrongPass1!",
        full_name: str = "Test User",
        role: SystemRole = SystemRole.member,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            password=password_manager.hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make_user


@pytest.fixture
def alice(make_user) -> User:
    """A regular member user persisted in the test DB."""
    return make_user(email="alice@example.com", full_name="Alice Smith")


@pytest.fixture
def admin_user(make_user) -> User:
    """An admin user persisted in the test DB."""
    return make_user(
        email="admin@example.com",
        full_name="Admin User",
        role=SystemRole.admin,
    )

