from app.repositories.project_repository import IProjectRepository
from app.services.project.interface import IProjectService
from app.models.Project import Project

class ProjectService(IProjectService):

    def __init__(self,repository:IProjectRepository = None):
        self.repository = repository


    def get_project(self, project_id):
        self.repository.get_by_id(project_id)

    def set_repository(self, repository:IProjectRepository):
        """Set the repository for this service."""
        self.repository = repository
    def create_project(self,project_data):
        project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=project_data.owner_id,
            created_at=project_data.created_at
        )
        return self.repository.save(project)

    def get_project_by_id(self, project_id):
        return self.repository.get_by_id(project_id)

    def get_all_projects(self, limit: int, offset: int):
        return self.repository.find_all(limit, offset)

    def update_project(self, project_id, project_data):
        return self.repository.update(project_id,project_data)

    def delete_project(self, project_id):
        return self.repository.delete(project_id)

    def get_project_by_name(self, name):
        return self.repository.get_by_name(name)

    def get_project_by_user(self, user_id):
        return self.repository.get_by_user(user_id)





