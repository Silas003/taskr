from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.models.Project import Project
class IProjectRepository(ABC):
    """Abstract base class defining the project repository contract."""

    @abstractmethod
    def add(self, project):
        """Add a new project to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, project_id):
        """Retrieve a project by ID."""
        pass

    @abstractmethod
    def update(self, project):
        """Update an existing project."""
        pass

    @abstractmethod
    def delete(self, project_id):
        """Delete a project by ID."""
        pass


class ProjectRepository(IProjectRepository):
    """SQLAlchemy-based implementation of IProjectRepository."""

    def __init__(self, db:Session):
        self.db = db

    def add(self, project):
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id):
        return self.db.get(Project,project_id)

    def update(self, project):
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id):
        project = self.get_by_id(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True