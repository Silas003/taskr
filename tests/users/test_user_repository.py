"""
Tests for UserRepository (app/repositories/user_repository.py)
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.models.User import User


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def repo(mock_db):
    return UserRepository(db=mock_db)


@pytest.fixture
def sample_user():
    user = User()
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.password = "hashed_password"
    return user


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------
class TestSave:
    def test_save_adds_commits_and_refreshes(self, repo, mock_db, sample_user):
        result = repo.save(sample_user)
        mock_db.add.assert_called_once_with(sample_user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_user)
        assert result is sample_user

    def test_save_returns_user(self, repo, mock_db, sample_user):
        mock_db.refresh.return_value = None  # refresh mutates in place
        result = repo.save(sample_user)
        assert result is sample_user


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------
class TestGetById:
    def test_returns_user_when_found(self, repo, mock_db, sample_user):
        mock_db.get.return_value = sample_user
        result = repo.get_by_id(1)
        mock_db.get.assert_called_once_with(User, 1)
        assert result is sample_user

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.get_by_id(999)
        assert result is None


# ---------------------------------------------------------------------------
# get_by_email()
# ---------------------------------------------------------------------------
class TestGetByEmail:
    def test_returns_user_when_found(self, repo, mock_db, sample_user):
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = sample_user

        result = repo.get_by_email("test@example.com")
        assert result is sample_user

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = repo.get_by_email("notfound@example.com")
        assert result is None

    def test_queries_user_model(self, repo, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        repo.get_by_email("test@example.com")
        mock_db.query.assert_called_once_with(User)


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------
class TestUpdate:
    def test_update_commits_and_refreshes(self, repo, mock_db, sample_user):
        result = repo.update(sample_user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_user)
        assert result is sample_user


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------
class TestDelete:
    def test_delete_returns_true_when_user_exists(self, repo, mock_db, sample_user):
        mock_db.get.return_value = sample_user
        result = repo.delete(1)
        mock_db.delete.assert_called_once_with(sample_user)
        mock_db.commit.assert_called_once()
        assert result is True

    def test_delete_returns_false_when_user_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.delete(999)
        mock_db.delete.assert_not_called()
        assert result is False


# ---------------------------------------------------------------------------
# find_all()
# ---------------------------------------------------------------------------
class TestFindAll:
    def test_find_all_applies_offset_and_limit(self, repo, mock_db, sample_user):
        mock_chain = mock_db.query.return_value
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = [sample_user]

        result = repo.find_all(limit=10, offset=0)
        mock_chain.offset.assert_called_once_with(0)
        mock_chain.limit.assert_called_once_with(10)
        assert result == [sample_user]

    def test_find_all_returns_empty_list(self, repo, mock_db):
        mock_chain = mock_db.query.return_value
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = []

        result = repo.find_all(limit=10, offset=0)
        assert result == []

    def test_find_all_pagination(self, repo, mock_db):
        mock_chain = mock_db.query.return_value
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = []

        repo.find_all(limit=5, offset=20)
        mock_chain.offset.assert_called_once_with(20)
        mock_chain.limit.assert_called_once_with(5)
