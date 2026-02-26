"""
Tests for TaskRepository (app/repositories/task_repository.py)
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.repositories.task_repository import TaskRepository
from app.models.Task import Task
from app.models.User import User
from app.models import Project


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def repo(mock_db):
    return TaskRepository(db=mock_db)


@pytest.fixture
def sample_task():
    t = Task()
    t.id = 1
    t.title = "Fix bug"
    t.description = "Something is broken"
    t.project_id = 1
    t.assigned_to = 2
    t.status = "pending"
    return t


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------
class TestSave:
    def test_adds_commits_refreshes(self, repo, mock_db, sample_task):
        result = repo.save(sample_task)
        mock_db.add.assert_called_once_with(sample_task)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_task)
        assert result is sample_task


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------
class TestGetById:
    def test_returns_task_when_found(self, repo, mock_db, sample_task):
        mock_db.get.return_value = sample_task
        result = repo.get_by_id(1)
        mock_db.get.assert_called_once_with(Task, 1)
        assert result is sample_task

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.get_by_id(999)
        assert result is None


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------
class TestUpdate:
    def test_updates_fields_and_returns_task(self, repo, mock_db, sample_task):
        mock_db.get.return_value = sample_task
        task_data = {"title": "Updated title", "status": "completed"}

        result = repo.update(1, task_data)

        assert sample_task.title == "Updated title"
        assert sample_task.status == "completed"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_task)
        assert result is sample_task

    def test_returns_none_when_task_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.update(999, {"title": "Ghost"})
        assert result is None
        mock_db.commit.assert_not_called()

    def test_partial_update_only_sets_provided_keys(self, repo, mock_db, sample_task):
        original_description = sample_task.description
        mock_db.get.return_value = sample_task
        repo.update(1, {"title": "New title"})
        assert sample_task.description == original_description


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------
class TestDelete:
    def test_deletes_and_returns_true(self, repo, mock_db, sample_task):
        mock_db.get.return_value = sample_task
        result = repo.delete(1)
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is True

    def test_returns_false_when_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.delete(999)
        mock_db.delete.assert_not_called()
        assert result is False


# ---------------------------------------------------------------------------
# find_all()
# NOTE: find_all() has a bug — it is missing `return`. Tests document this.
# ---------------------------------------------------------------------------
class TestFindAll:
    def test_find_all_returns_none_due_to_missing_return(self, repo, mock_db, sample_task):
        mock_chain = mock_db.query.return_value
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = [sample_task]
        # Bug: find_all does not return the result
        result = repo.find_all(skip=0, limit=10)
        assert result is None

    def test_find_all_applies_offset_and_limit(self, repo, mock_db):
        mock_chain = mock_db.query.return_value
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = []
        repo.find_all(skip=5, limit=20)
        mock_chain.offset.assert_called_once_with(5)
        mock_chain.limit.assert_called_once_with(20)


# ---------------------------------------------------------------------------
# get_task_by_user()
# ---------------------------------------------------------------------------
class TestGetTaskByUser:
    def test_returns_user_tasks(self, repo, mock_db, sample_task):
        mock_user = MagicMock(spec=User)
        mock_user.tasks = [sample_task]
        mock_db.get.return_value = mock_user
        result = repo.get_task_by_user(1)
        assert result == [sample_task]

    def test_returns_empty_list_when_user_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.get_task_by_user(999)
        assert result == []


# ---------------------------------------------------------------------------
# get_task_by_project()
# ---------------------------------------------------------------------------
class TestGetTaskByProject:
    def test_returns_project_tasks(self, repo, mock_db, sample_task):
        mock_project = MagicMock(spec=Project)
        mock_project.tasks = [sample_task]
        mock_db.get.return_value = mock_project
        result = repo.get_task_by_project(1)
        assert result == [sample_task]

    def test_returns_empty_list_when_project_not_found(self, repo, mock_db):
        mock_db.get.return_value = None
        result = repo.get_task_by_project(999)
        assert result == []
