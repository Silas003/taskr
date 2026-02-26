from app.repositories.project_repository import IProjectRepository
from app.schemas.UserSchema import ProjectRole
from app.services.project.interface import IProjectService
from app.models.Project import Project, ProjectMember


class ProjectService(IProjectService):

    def __init__(self,repository:IProjectRepository = None):
        self.repository = repository


    def get_project(self, project_id):
        self.repository.get_by_id(project_id)

    def set_repository(self, repository:IProjectRepository):
        """Set the repository for this service."""
        self.repository = repository
    def create_project(self,project_data)->Project:
        project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=project_data.owner_id,
            created_at=project_data.created_at
        )
        project = self.repository.save(project)
        project_member = ProjectMember(
            project_id=project.id,
            user_id=project_data.owner_id,
            role=ProjectRole.owner
        )
        self.repository.save_user_to_project(project_member)
        return project


    def get_project_by_id(self, project_id):
        return self.repository.get_by_id(project_id)

    def get_all_projects(self, skip: int = 0, limit: int = 10):
        return self.repository.find_all(skip=skip, limit=limit)

    def update_project(self, project_id, project_data):
        return self.repository.update(project_id,project_data)

    def delete_project(self, project_id):
        return self.repository.delete(project_id)

    def get_project_by_name(self, name):
        return self.repository.get_by_name(name)

    def get_project_by_user(self, user_id):
        return self.repository.get_by_user(user_id)





