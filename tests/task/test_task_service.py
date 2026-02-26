"""
Tests for TaskService (app/services/task/implementation.py)
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.models.Task import Task
from app.schemas.dto import TaskCreate, TaskBase, TaskStatusEnum
from app.services.task.implementation import TaskService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    svc = TaskService(repository=mock_repo)
    return svc


@pytest.fixture
def sample_task():
    t = Task()
    t.id = 1
    t.title = "Fix bug"
    t.description = "Something broken"
    t.project_id = 2
    t.assigned_to = 5
    t.status = "pending"
    t.due_date = None
    t.created_at = datetime(2024, 1, 1)
    return t


@pytest.fixture
def task_create():
    return TaskCreate(
        title="Fix bug",
        description="Something broken",
        project_id=2,
        assigned_to=5,
        status=TaskStatusEnum.pending,
        due_date=None,
        created_at=datetime(2024, 1, 1),
    )


@pytest.fixture
def task_base():
    return TaskBase(
        title="Fix bug",
        description="Something broken",
        project_id=2,
        assigned_to=5,
        status=TaskStatusEnum.pending,
        due_date=None,
        created_at=datetime(2024, 1, 1),
    )


# ---------------------------------------------------------------------------
# __init__ / set_repository
# ---------------------------------------------------------------------------
class TestInit:
    def test_default_repository_is_none(self):
        svc = TaskService()
        assert svc.repository is None

    def test_set_repository(self, service):
        new_repo = MagicMock()
        service.set_repository(new_repo)
        assert service.repository is new_repo


# ---------------------------------------------------------------------------
# create_task()
# ---------------------------------------------------------------------------
class TestCreateTask:
    def test_creates_task_successfully(self, service, mock_repo, task_create, sample_task):
        mock_repo.save.return_value = sample_task
        result = service.create_task(task_create)
        mock_repo.save.assert_called_once()
        assert result is sample_task

    def test_saved_task_has_correct_title(self, service, mock_repo, task_create, sample_task):
        mock_repo.save.return_value = sample_task
        service.create_task(task_create)
        saved: Task = mock_repo.save.call_args[0][0]
        assert saved.title == task_create.title

    def test_saved_task_status_is_string_value(self, service, mock_repo, task_create, sample_task):
        mock_repo.save.return_value = sample_task
        service.create_task(task_create)
        saved: Task = mock_repo.save.call_args[0][0]
        assert saved.status == "pending"

    def test_saved_task_assigned_to_can_be_none(self, service, mock_repo, sample_task):
        task_in = TaskCreate(
            title="Unassigned",
            project_id=1,
            status=TaskStatusEnum.pending,
            created_at=datetime(2024, 1, 1),
        )
        mock_repo.save.return_value = sample_task
        service.create_task(task_in)
        saved: Task = mock_repo.save.call_args[0][0]
        assert saved.assigned_to is None

    def test_saved_task_correct_project_id(self, service, mock_repo, task_create, sample_task):
        mock_repo.save.return_value = sample_task
        service.create_task(task_create)
        saved: Task = mock_repo.save.call_args[0][0]
        assert saved.project_id == task_create.project_id

    def test_saved_task_preserves_created_at(self, service, mock_repo, task_create, sample_task):
        mock_repo.save.return_value = sample_task
        service.create_task(task_create)
        saved: Task = mock_repo.save.call_args[0][0]
        assert saved.created_at == task_create.created_at


# ---------------------------------------------------------------------------
# get_task()
# ---------------------------------------------------------------------------
class TestGetTask:
    def test_returns_task_when_found(self, service, mock_repo, sample_task):
        mock_repo.get_by_id.return_value = sample_task
        result = service.get_task(1)
        mock_repo.get_by_id.assert_called_once_with(1)
        assert result is sample_task

    def test_returns_none_when_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        result = service.get_task(999)
        assert result is None


# ---------------------------------------------------------------------------
# update_task()
# ---------------------------------------------------------------------------
class TestUpdateTask:
    def test_delegates_to_repository(self, service, mock_repo, task_base, sample_task):
        mock_repo.update.return_value = sample_task
        result = service.update_task(1, task_base)
        mock_repo.update.assert_called_once_with(1, task_base.dict(exclude_unset=True))
        assert result is sample_task

    def test_returns_none_when_task_not_found(self, service, mock_repo, task_base):
        mock_repo.update.return_value = None
        result = service.update_task(999, task_base)
        assert result is None


# ---------------------------------------------------------------------------
# delete_task()
# ---------------------------------------------------------------------------
class TestDeleteTask:
    def test_returns_true_when_deleted(self, service, mock_repo):
        mock_repo.delete.return_value = True
        result = service.delete_task(1)
        mock_repo.delete.assert_called_once_with(1)
        assert result is True

    def test_returns_false_when_not_found(self, service, mock_repo):
        mock_repo.delete.return_value = False
        result = service.delete_task(999)
        assert result is False


# ---------------------------------------------------------------------------
# get_all_tasks()
# ---------------------------------------------------------------------------
class TestGetAllTasks:
    def test_returns_tasks(self, service, mock_repo, sample_task):
        mock_repo.find_all.return_value = [sample_task]
        result = service.get_all_tasks(limit=10, offset=0)
        mock_repo.find_all.assert_called_once_with(10, 0)
        assert result == [sample_task]

    def test_passes_limit_and_offset(self, service, mock_repo):
        mock_repo.find_all.return_value = []
        service.get_all_tasks(limit=5, offset=20)
        mock_repo.find_all.assert_called_once_with(5, 20)

    def test_returns_empty_list(self, service, mock_repo):
        mock_repo.find_all.return_value = []
        result = service.get_all_tasks(limit=10, offset=0)
        assert result == []


# ---------------------------------------------------------------------------
# get_task_by_user()
# ---------------------------------------------------------------------------
class TestGetTaskByUser:
    def test_returns_user_tasks(self, service, mock_repo, sample_task):
        mock_repo.get_task_by_user.return_value = [sample_task]
        result = service.get_task_by_user(5)
        mock_repo.get_task_by_user.assert_called_once_with(5)
        assert result == [sample_task]

    def test_returns_empty_list(self, service, mock_repo):
        mock_repo.get_task_by_user.return_value = []
        result = service.get_task_by_user(999)
        assert result == []


# ---------------------------------------------------------------------------
# get_task_by_project()
# ---------------------------------------------------------------------------
class TestGetTaskByProject:
    def test_returns_project_tasks(self, service, mock_repo, sample_task):
        mock_repo.get_task_by_project.return_value = [sample_task]
        result = service.get_task_by_project(2)
        mock_repo.get_task_by_project.assert_called_once_with(2)
        assert result == [sample_task]

    def test_returns_empty_list(self, service, mock_repo):
        mock_repo.get_task_by_project.return_value = []
        result = service.get_task_by_project(999)
        assert result == []
