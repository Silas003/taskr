from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.models.Project import Project, ProjectMember
from app.models.User import User
from typing import Optional, List
from app.exceptions.CustomExceptions import  EntityNotFound
from app.schemas.UserSchema import ProjectRole
class IProjectRepository(ABC):
    """Abstract base class defining the project repository contract."""

    @abstractmethod
    def save(self, project):
        """Add a new project to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, project_id):
        """Retrieve a project by ID."""
        pass

    @abstractmethod
    def update(self,id, project):
        """Update an existing project."""
        pass

    @abstractmethod
    def delete(self, project_id):
        """Delete a project by ID."""
        pass

    @abstractmethod
    def find_all(self,skip:int,limit:int):
        """Retrieve all projects with pagination."""
        pass

    @abstractmethod
    def get_by_user(self,user_id):
        """Retrieve all projects by user."""
        pass

    @abstractmethod
    def get_by_name(self,name):
        """Retrieve all projects by name."""
        pass

    @abstractmethod
    def save_user_to_project(self,project_member:ProjectMember):
        """Save user to project."""
        pass

    @abstractmethod
    def get_member(self, project_id: int, user_id: int) -> Optional[ProjectMember]:
        """Retrieve a specific member of a project."""
        pass

    @abstractmethod
    def update_member_role(self, project_id: int, user_id: int, role: ProjectRole) -> ProjectMember:
        """Update the role of a project member."""
        pass

    @abstractmethod
    def remove_member(self, project_id: int, user_id: int) -> bool:
        """Remove a member from a project."""
        pass
    @abstractmethod
    def create_project_with_owner(self, project: Project, member: ProjectMember) -> Project:
        """Create a new project with an owner."""

class ProjectRepository(IProjectRepository):
    """SQLAlchemy-based implementation of IProjectRepository."""

    def __init__(self, db:Session):
        self.db = db

    def save(self, project:Project)->Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id):
        return self.db.query(Project).filter(Project.id==project_id).first()

    def update(self,id, project):
        db_project = self.get_by_id(id)
        if not db_project:
            return EntityNotFound("project",id)
        for key,value in project.items():
            setattr(project,key,value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: int) -> bool:
        try:
            project = self.get_by_id(project_id)
            if not project:
                return False
            self.db.delete(project)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def find_all(self, skip: int = 0, limit: int = 10):
        return self.db.query(Project).offset(skip).limit(limit).all()

    def get_by_user(self,user_id)->List[Optional[Project]]:
        user = self.db.get(User,user_id)
        if user is not None:
            return user.projects
        return []

    def get_by_name(self,name)->Optional[Project]:
        return self.db.query(Project).filter(Project.name==name).first()

    def save_user_to_project(self, project_member: ProjectMember):
        try:
            project = self.get_by_id(project_member.project_id)
            if not project:
                raise EntityNotFound("project", project_member.project_id)
            user = self.db.get(User, project_member.user_id)
            if not user:
                raise EntityNotFound("user", project_member.user_id)
            self.db.add(project_member)
            self.db.commit()
            self.db.refresh(project_member)
            return project_member
        except EntityNotFound:
            raise
        except Exception:
            self.db.rollback()
            raise

    def get_member(self, project_id: int, user_id: int) -> Optional[ProjectMember]:
        return (
            self.db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            .first()
        )

    def update_member_role(self, project_id, user_id, role):
        try:
            member = (
                self.db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                )
                .with_for_update()        # ← locks the row until commit
                .first()
            )
            if not member:
                raise EntityNotFound("project_member", f"{project_id}:{user_id}")
            member.role = role.value if hasattr(role, "value") else str(role)
            self.db.commit()
            self.db.refresh(member)
            return member
        except EntityNotFound:
            raise
        except Exception:
            self.db.rollback()
            raise

    def remove_member(self, project_id: int, user_id: int) -> bool:
        member = self.get_member(project_id, user_id)
        if not member:
            return False
        self.db.delete(member)
        self.db.commit()
        return True

    def create_project_with_owner(self, project: Project, member: ProjectMember) -> Project:
        try:
            self.db.add(project)
            self.db.flush()                    # assigns project.id without committing
            member.project_id = project.id
            self.db.add(member)
            self.db.commit()                   # single commit — both or neither
            self.db.refresh(project)
            return project
        except Exception:
            self.db.rollback()
            raise


