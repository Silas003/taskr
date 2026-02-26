"""
Tests for ProjectRepository (app/repositories/project_repository.py)
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.models.Project import Project, ProjectMember
from app.models.User import User
from app.schemas.UserSchema import ProjectRole
from app.exceptions.CustomExceptions import EntityNotFound


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def repo(mock_db):
    return ProjectRepository(db=mock_db)


@pytest.fixture
def sample_project():
    p = Project()
    p.id = 1
    p.name = "Test Project"
    p.description = "A test project"
    p.owner_id = 1
    return p


@pytest.fixture
def sample_member():
    m = ProjectMember()
    m.project_id = 1
    m.user_id = 2
    m.role = ProjectRole.editor
    return m


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------
class TestSave:
    def test_save_adds_commits_refreshes(self, repo, mock_db, sample_project):
        result = repo.save(sample_project)
        mock_db.add.assert_called_once_with(sample_project)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_project)
        assert result is sample_project


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------
class TestGetById:
    def test_returns_project_when_found(self, repo, mock_db, sample_project):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        result = repo.get_by_id(1)
        assert result is sample_project

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = repo.get_by_id(999)
        assert result is None


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------
class TestDelete:
    def test_delete_returns_true_when_found(self, repo, mock_db, sample_project):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        result = repo.delete(1)
        mock_db.delete.assert_called_once_with(sample_project)
        mock_db.commit.assert_called_once()
        assert result is True

    def test_delete_returns_false_when_not_found(self, repo, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = repo.delete(999)
        mock_db.delete.assert_not_called()
        assert result is False


# ---------------------------------------------------------------------------
# find_all()
# ---------------------------------------------------------------------------
class TestFindAll:
    def test_applies_offset_and_limit(self, repo, mock_db, sample_project):
        mock_chain = mock_db.query.return_value
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = [sample_project]

        result = repo.find_all(skip=5, limit=10)
        mock_chain.offset.assert_called_once_with(5)
        mock_chain.limit.assert_called_once_with(10)
        assert result == [sample_project]

    def test_returns_empty_list(self, repo, mock_db):
        mock_chain = mock_db.query.return_value
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = []

        result = repo.find_all(skip=0, limit=10)
        assert result == []


# ---------------------------------------------------------------------------
# get_by_user()
# ---------------------------------------------------------------------------
class TestGetByUser:
    def test_returns_user_projects(self, repo, mock_db, sample_project):
        mock_user = MagicMock(spec=User)
        mock_user.projects = [sample_project]
        mock_db.get.return_value = mock_user

        result = repo.get_by_user(1)
        assert result == [sample_project]

    def test_returns_empty_list_when_user_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.get_by_user(999)
        assert result == []


# ---------------------------------------------------------------------------
# get_by_name()
# ---------------------------------------------------------------------------
class TestGetByName:
    def test_returns_project_when_found(self, repo, mock_db, sample_project):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        result = repo.get_by_name("Test Project")
        assert result is sample_project

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = repo.get_by_name("Ghost")
        assert result is None


# ---------------------------------------------------------------------------
# save_user_to_project()
# ---------------------------------------------------------------------------
class TestSaveUserToProject:
    def test_saves_member_successfully(self, repo, mock_db, sample_project, sample_member):
        # project found, user found
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_db.get.return_value = MagicMock(spec=User)

        result = repo.save_user_to_project(sample_member)
        mock_db.add.assert_called_once_with(sample_member)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_member)
        assert result is sample_member

    def test_raises_entity_not_found_when_project_missing(self, repo, mock_db, sample_member):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(EntityNotFound):
            repo.save_user_to_project(sample_member)

    def test_raises_entity_not_found_when_user_missing(self, repo, mock_db, sample_project, sample_member):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_db.get.return_value = None
        with pytest.raises(EntityNotFound):
            repo.save_user_to_project(sample_member)


# ---------------------------------------------------------------------------
# get_member()
# ---------------------------------------------------------------------------
class TestGetMember:
    def test_returns_member_when_found(self, repo, mock_db, sample_member):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member
        result = repo.get_member(1, 2)
        assert result is sample_member

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = repo.get_member(1, 999)
        assert result is None


# ---------------------------------------------------------------------------
# update_member_role()
# ---------------------------------------------------------------------------
class TestUpdateMemberRole:
    def test_updates_role_successfully(self, repo, mock_db, sample_member):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member
        result = repo.update_member_role(1, 2, ProjectRole.viewer)
        assert sample_member.role == ProjectRole.viewer.value
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_member)
        assert result is sample_member

    def test_raises_entity_not_found_when_member_missing(self, repo, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(EntityNotFound):
            repo.update_member_role(1, 999, ProjectRole.editor)


# ---------------------------------------------------------------------------
# remove_member()
# ---------------------------------------------------------------------------
class TestRemoveMember:
    def test_removes_member_returns_true(self, repo, mock_db, sample_member):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member
        result = repo.remove_member(1, 2)
        mock_db.delete.assert_called_once_with(sample_member)
        mock_db.commit.assert_called_once()
        assert result is True

    def test_returns_false_when_member_not_found(self, repo, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = repo.remove_member(1, 999)
        mock_db.delete.assert_not_called()
        assert result is False
