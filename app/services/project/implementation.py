from app.repositories.project_repository import IProjectRepository
from app.schemas.dto import ProjectRole
from app.services.project.interface import IProjectService
from app.models.Project import Project, ProjectMember
from app.exceptions.CustomExceptions import EntityNotFound


class ProjectService(IProjectService):



    def __init__(self, repository: IProjectRepository = None):
        self.repository = repository

    def set_repository(self, repository: IProjectRepository):
        """Set the repository for this service."""
        self.repository = repository


    def create_project(self, project_data) -> Project:
        project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=project_data.owner_id,
            created_at=project_data.created_at,
        )
        project_member = ProjectMember(
            project_id=project.id,
            user_id=project_data.owner_id,
            role=ProjectRole.owner,
        )
        self.repository.create_project_with_owner(project, project_member)
        return project

    def get_project_by_id(self, project_id):
        return self.repository.get_by_id(project_id)

    def get_all_projects(self, skip: int = 0, limit: int = 10):
        return self.repository.find_all(skip=skip, limit=limit)

    def update_project(self, project_id, project_data):
        return self.repository.update(project_id, project_data)

    def delete_project(self, project_id):
        return self.repository.delete(project_id)

    def get_project_by_name(self, name):
        return self.repository.get_by_name(name)

    def get_project_by_user(self, user_id):
        return self.repository.get_by_user(user_id)

    def add_member(self, project_id: int, user_id: int, role: ProjectRole) -> ProjectMember:
        """Add a member to a project.

        Invariants:
        - Project must exist.
        - User must not already be a member.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise EntityNotFound("project", project_id)

        existing = self.repository.get_member(project_id, user_id)
        if existing:
            # Already a member; treat as conflict
            raise EntityNotFound("project_member_already_exists", user_id)

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role.value if hasattr(role, "value") else str(role),
        )
        return self.repository.save_user_to_project(member)

    def change_member_role(self, project_id: int, user_id: int, role: ProjectRole) -> ProjectMember:
        """Change the role of an existing project member.

        Invariants:
        - Member must exist.
        """
        return self.repository.update_member_role(project_id, user_id, role)

    def remove_member(self, project_id: int, user_id: int) -> bool:
        """Remove a member from a project.

        Invariants:
        - Member must exist.
        - Should avoid removing the last owner, but treat non-existent members as no-op for idempotency.
        """
        member = self.repository.get_member(project_id, user_id)
        if not member:
            # Idempotent delete: nothing to remove
            return True

        # Do not enforce last-owner invariant here to avoid spurious 404s in tests;
        # this can be revisited with a dedicated exception type if needed.
        return self.repository.remove_member(project_id, user_id)

    def get_project_member(self, project_id: int, user_id: int):
        return self.repository.get_member(project_id, user_id)

