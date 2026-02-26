"""
Tests for ProjectService (app/services/project/implementation.py)
"""
import pytest
from unittest.mock import MagicMock

from app.services.project.implementation import ProjectService
from app.models.Project import Project, ProjectMember
from app.schemas.dto import ProjectRole
from app.exceptions.CustomExceptions import EntityNotFound


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    svc = ProjectService(repository=mock_repo)
    return svc


@pytest.fixture
def sample_project():
    p = Project()
    p.id = 1
    p.name = "Alpha"
    p.description = "Alpha project"
    p.owner_id = 10
    return p


@pytest.fixture
def sample_member():
    m = ProjectMember()
    m.project_id = 1
    m.user_id = 2
    m.role = ProjectRole.editor.value
    return m


@pytest.fixture
def project_data():
    data = MagicMock()
    data.name = "Alpha"
    data.description = "Alpha project"
    data.owner_id = 10
    data.created_at = None
    return data


# ---------------------------------------------------------------------------
# __init__ / set_repository
# ---------------------------------------------------------------------------
class TestInit:
    def test_default_repository_is_none(self):
        svc = ProjectService()
        assert svc.repository is None

    def test_set_repository(self, service):
        new_repo = MagicMock()
        service.set_repository(new_repo)
        assert service.repository is new_repo


# ---------------------------------------------------------------------------
# create_project()
# ---------------------------------------------------------------------------
class TestCreateProject:
    def test_creates_project_and_adds_owner_as_member(self, service, mock_repo, project_data, sample_project, sample_member):
        # New impl uses create_project_with_owner — single atomic call
        mock_repo.create_project_with_owner.return_value = sample_project

        result = service.create_project(project_data)

        mock_repo.create_project_with_owner.assert_called_once()
        # result is the local project object built in the service, not the repo return value
        assert result.name == project_data.name
        assert result.owner_id == project_data.owner_id

    def test_saved_project_has_correct_fields(self, service, mock_repo, project_data, sample_project):
        mock_repo.create_project_with_owner.return_value = sample_project

        service.create_project(project_data)

        # Use .args for reliable positional arg access across all mock versions
        saved_project: Project = mock_repo.create_project_with_owner.call_args.args[0]
        assert saved_project.name == project_data.name
        assert saved_project.owner_id == project_data.owner_id

    def test_owner_added_as_owner_role(self, service, mock_repo, project_data, sample_project):
        mock_repo.create_project_with_owner.return_value = sample_project

        service.create_project(project_data)

        saved_member: ProjectMember = mock_repo.create_project_with_owner.call_args.args[1]
        assert saved_member.role == ProjectRole.owner
        assert saved_member.user_id == project_data.owner_id


# ---------------------------------------------------------------------------
# get_project_by_id()
# ---------------------------------------------------------------------------
class TestGetProjectById:
    def test_returns_project(self, service, mock_repo, sample_project):
        mock_repo.get_by_id.return_value = sample_project
        result = service.get_project_by_id(1)
        mock_repo.get_by_id.assert_called_once_with(1)
        assert result is sample_project

    def test_returns_none_when_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        result = service.get_project_by_id(999)
        assert result is None


# ---------------------------------------------------------------------------
# get_all_projects()
# ---------------------------------------------------------------------------
class TestGetAllProjects:
    def test_returns_list(self, service, mock_repo, sample_project):
        mock_repo.find_all.return_value = [sample_project]
        result = service.get_all_projects(skip=0, limit=10)
        mock_repo.find_all.assert_called_once_with(skip=0, limit=10)
        assert result == [sample_project]

    def test_passes_pagination_params(self, service, mock_repo):
        mock_repo.find_all.return_value = []
        service.get_all_projects(skip=20, limit=5)
        mock_repo.find_all.assert_called_once_with(skip=20, limit=5)

    def test_returns_empty_list(self, service, mock_repo):
        mock_repo.find_all.return_value = []
        result = service.get_all_projects()
        assert result == []


# ---------------------------------------------------------------------------
# update_project()
# ---------------------------------------------------------------------------
class TestUpdateProject:
    def test_delegates_to_repository(self, service, mock_repo, sample_project, project_data):
        mock_repo.update.return_value = sample_project
        result = service.update_project(1, project_data)
        mock_repo.update.assert_called_once_with(1, project_data)
        assert result is sample_project


# ---------------------------------------------------------------------------
# delete_project()
# ---------------------------------------------------------------------------
class TestDeleteProject:
    def test_returns_true_when_deleted(self, service, mock_repo):
        mock_repo.delete.return_value = True
        result = service.delete_project(1)
        mock_repo.delete.assert_called_once_with(1)
        assert result is True

    def test_returns_false_when_not_found(self, service, mock_repo):
        mock_repo.delete.return_value = False
        result = service.delete_project(999)
        assert result is False


# ---------------------------------------------------------------------------
# get_project_by_name()
# ---------------------------------------------------------------------------
class TestGetProjectByName:
    def test_returns_project(self, service, mock_repo, sample_project):
        mock_repo.get_by_name.return_value = sample_project
        result = service.get_project_by_name("Alpha")
        mock_repo.get_by_name.assert_called_once_with("Alpha")
        assert result is sample_project

    def test_returns_none_when_not_found(self, service, mock_repo):
        mock_repo.get_by_name.return_value = None
        result = service.get_project_by_name("Ghost")
        assert result is None


# ---------------------------------------------------------------------------
# get_project_by_user()
# ---------------------------------------------------------------------------
class TestGetProjectByUser:
    def test_returns_user_projects(self, service, mock_repo, sample_project):
        mock_repo.get_by_user.return_value = [sample_project]
        result = service.get_project_by_user(10)
        mock_repo.get_by_user.assert_called_once_with(10)
        assert result == [sample_project]

    def test_returns_empty_list(self, service, mock_repo):
        mock_repo.get_by_user.return_value = []
        result = service.get_project_by_user(999)
        assert result == []


# ---------------------------------------------------------------------------
# add_member()
# ---------------------------------------------------------------------------
class TestAddMember:
    def test_adds_member_successfully(self, service, mock_repo, sample_project, sample_member):
        mock_repo.get_by_id.return_value = sample_project
        mock_repo.get_member.return_value = None
        mock_repo.save_user_to_project.return_value = sample_member

        result = service.add_member(1, 2, ProjectRole.editor)

        mock_repo.save_user_to_project.assert_called_once()
        assert result is sample_member

    def test_raises_when_project_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(EntityNotFound):
            service.add_member(999, 2, ProjectRole.editor)

    def test_raises_when_user_already_member(self, service, mock_repo, sample_project, sample_member):
        mock_repo.get_by_id.return_value = sample_project
        mock_repo.get_member.return_value = sample_member  # already exists

        with pytest.raises(EntityNotFound):
            service.add_member(1, 2, ProjectRole.editor)

        mock_repo.save_user_to_project.assert_not_called()

    def test_new_member_has_correct_role(self, service, mock_repo, sample_project, sample_member):
        mock_repo.get_by_id.return_value = sample_project
        mock_repo.get_member.return_value = None
        mock_repo.save_user_to_project.return_value = sample_member

        service.add_member(1, 2, ProjectRole.viewer)

        created: ProjectMember = mock_repo.save_user_to_project.call_args[0][0]
        assert created.role == ProjectRole.viewer.value

    def test_new_member_has_correct_project_and_user_ids(self, service, mock_repo, sample_project, sample_member):
        mock_repo.get_by_id.return_value = sample_project
        mock_repo.get_member.return_value = None
        mock_repo.save_user_to_project.return_value = sample_member

        service.add_member(1, 42, ProjectRole.editor)

        created: ProjectMember = mock_repo.save_user_to_project.call_args[0][0]
        assert created.project_id == 1
        assert created.user_id == 42


# ---------------------------------------------------------------------------
# change_member_role()
# ---------------------------------------------------------------------------
class TestChangeMemberRole:
    def test_delegates_to_repository(self, service, mock_repo, sample_member):
        mock_repo.update_member_role.return_value = sample_member
        result = service.change_member_role(1, 2, ProjectRole.viewer)
        mock_repo.update_member_role.assert_called_once_with(1, 2, ProjectRole.viewer)
        assert result is sample_member

    def test_raises_when_member_not_found(self, service, mock_repo):
        mock_repo.update_member_role.side_effect = EntityNotFound("project_member", "1:999")
        with pytest.raises(EntityNotFound):
            service.change_member_role(1, 999, ProjectRole.viewer)


# ---------------------------------------------------------------------------
# remove_member()
# ---------------------------------------------------------------------------
class TestRemoveMember:
    def test_removes_existing_member(self, service, mock_repo, sample_member):
        mock_repo.get_member.return_value = sample_member
        mock_repo.remove_member.return_value = True

        result = service.remove_member(1, 2)
        mock_repo.remove_member.assert_called_once_with(1, 2)
        assert result is True

    def test_idempotent_when_member_not_found(self, service, mock_repo):
        mock_repo.get_member.return_value = None

        result = service.remove_member(1, 999)
        mock_repo.remove_member.assert_not_called()
        assert result is True
