from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Project
from app.repositories.project_repository import ProjectRepository
from app.routers.users import get_current_user, require_project_role
from app.schemas.UserSchema import ProjectCreate, ProjectRole
from app.schemas.response import ResponseBase
from app.services.project.implementation import ProjectService

router = APIRouter(
    tags=["Projects"],
    prefix="/project"
)


def project_access_control(
        id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> Project:
    project = db.query(Project).filter(Project.id == id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id == current_user.id:
        return project

    member_record = next(
        (m for m in getattr(project, "members", []) if m.user_id == current_user.id),
        None
    )
    if member_record and member_record.role in (ProjectRole.editor, ProjectRole.viewer):
        return project

    raise HTTPException(status_code=403, detail="You do not have access to this project")


def get_project_service(db: Session = Depends(get_db)):
    service = ProjectService()
    service.set_repository(ProjectRepository(db))
    return service


@router.get("/all", dependencies=[Depends(get_current_user)])
def get_all_projects(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=100),
        service: ProjectService = Depends(get_project_service)
):
    return service.get_all_projects(skip=skip, limit=limit)


@router.get("/{id}")
def get_project(
        id: int,
        project: Project = Depends(project_access_control),
        service: ProjectService = Depends(get_project_service)
):
    prj = service.get_project_by_id(id)
    return ResponseBase(code=200, message="Project retrieved successfully", data=prj)

# 3. Create a project
@router.post("", dependencies=[Depends(get_current_user)], status_code=HTTPStatus.CREATED)
def create_project(
        project_data: ProjectCreate,
        service: ProjectService = Depends(get_project_service)
) -> ResponseBase:
    project = service.create_project(project_data)
    return ResponseBase(code=201, message="Project created successfully", data=project)


# 4. Update a project
@router.put("/{id}", dependencies=[Depends(get_current_user),
                                   Depends(require_project_role(ProjectRole.owner, ProjectRole.editor))])
def update_project(
        id: int,
        project_data: ProjectCreate,  # assuming same schema as create
        service: ProjectService = Depends(get_project_service)
):
    return service.update_project(id, project_data)


# 5. Delete a project
@router.delete("/{id}", dependencies=[Depends(get_current_user), Depends(require_project_role(ProjectRole.owner))])
def delete_project(id: int, service: ProjectService = Depends(get_project_service)):
    return service.delete_project(id)


# 6. Get projects by user
@router.get("/user/{user_id}", dependencies=[Depends(get_current_user),
                                             Depends(require_project_role(ProjectRole.owner, ProjectRole.viewer))])
def get_projects_by_user(user_id: int, service: ProjectService = Depends(get_project_service)):
    return service.get_project_by_user(user_id)


# 7. Get project by name
@router.get("/by-name", dependencies=[Depends(get_current_user),
                                      Depends(require_project_role(ProjectRole.owner, ProjectRole.viewer))])
def get_project_by_name(name: str, service: ProjectService = Depends(get_project_service)):
    return service.get_project_by_name(name)