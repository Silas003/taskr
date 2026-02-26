from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Project
from app.repositories.project_repository import ProjectRepository
from app.routers.v1.users import get_current_user, require_project_role
from app.schemas.dto import (
    ProjectCreate,
    ProjectRole,
    ProjectRead,
    ProjectMemberAdd,
    ProjectMemberUpdate,
    ProjectMemberRead,
    SystemRole,
)
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


def require_project_membership_admin(
        id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> Project:
    """Ensure the actor can manage project members (owner or system admin)."""
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role == SystemRole.admin or project.owner_id == current_user.id:
        return project

    raise HTTPException(status_code=403, detail="You do not have permission to manage members for this project")



@router.get(
    "/by-name",
    dependencies=[Depends(get_current_user)],
    response_model=ResponseBase[ProjectRead],
    summary="Get project by name",
    description="Retrieve a single project by its unique name.",
    responses={
        200: {
            "description": "Project retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Project retrieved successfully",
                        "data": {
                            "id": 1,
                            "name": "Membership Project",
                            "description": "Project for membership tests",
                            "owner_id": 1,
                        },
                    }
                }
            },
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            },
        },
    },
)
def get_project_by_name(name: str, service: ProjectService = Depends(get_project_service)):
    project = service.get_project_by_name(name)
    return ResponseBase(code=200, message="Project retrieved successfully", data=project)


@router.get(
    "/all",
    dependencies=[Depends(get_current_user)],
    status_code=HTTPStatus.OK,
    response_model=ResponseBase[List[ProjectRead]],
    summary="List all projects",
    description=(
        "List projects with pagination.\n\n"
        "Accessible to authenticated users; visibility may be filtered in service layer."
    ),
    responses={
        200: {
            "description": "Projects retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Projects retrieved successfully",
                        "data": [
                            {
                                "id": 1,
                                "name": "Membership Project",
                                "description": "Project for membership tests",
                                "owner_id": 1,
                            }
                        ],
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
def get_all_projects(
        skip: int = Query(default=0, ge=0, description="Items to skip for pagination"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum projects to return"),
        service: ProjectService = Depends(get_project_service)
):
    projects = service.get_all_projects(skip=skip, limit=limit)
    return ResponseBase(code=200, message="Projects retrieved successfully", data=projects)


@router.get(
    "/{id}",
    response_model=ResponseBase[ProjectRead],
    summary="Get project by id",
    description=(
        "Retrieve a single project by its id.\n\n"
        "Requires that the current user is the owner or a member with sufficient project role."
    ),
    responses={
        200: {
            "description": "Project retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Project retrieved successfully",
                        "data": {
                            "id": 1,
                            "name": "Membership Project",
                            "description": "Project for membership tests",
                            "owner_id": 1,
                        },
                    }
                }
            },
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            },
        },
        403: {
            "description": "Forbidden – user has no access to this project",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have access to this project"}
                }
            },
        },
    },
)
def get_project(
        id: int,
        project: Project = Depends(project_access_control),
        service: ProjectService = Depends(get_project_service)
):
    prj = service.get_project_by_id(id)
    return ResponseBase(code=200, message="Project retrieved successfully", data=prj)


@router.post(
    "",
    dependencies=[Depends(get_current_user)],
    status_code=HTTPStatus.CREATED,
    response_model=ResponseBase[ProjectRead],
    summary="Create a new project",
    description="Create a new project with the current user as owner.",
    responses={
        201: {
            "description": "Project created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 201,
                        "message": "Project created successfully",
                        "data": {
                            "id": 1,
                            "name": "New Project",
                            "description": "Project description",
                            "owner_id": 1,
                        },
                    }
                }
            },
        },
        400: {
            "description": "Bad request (e.g. duplicate project name)",
            "content": {
                "application/json": {
                    "example": {"detail": "Project name already exists"}
                }
            },
        },
    },
)
def create_project(
        project_data: ProjectCreate,
        service: ProjectService = Depends(get_project_service)
) -> ResponseBase:
    project = service.create_project(project_data)
    return ResponseBase(code=201, message="Project created successfully", data=project)


@router.put(
    "/{id}",
    dependencies=[Depends(get_current_user),
                  Depends(require_project_role(ProjectRole.owner, ProjectRole.editor))],
    response_model=ResponseBase[ProjectRead],
    status_code=HTTPStatus.OK,
    summary="Update a project",
    description="Update project details. Requires owner or editor project role.",
    responses={
        200: {
            "description": "Project updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Project updated successfully",
                        "data": {
                            "id": 1,
                            "name": "Updated Project",
                            "description": "Updated description",
                            "owner_id": 1,
                        },
                    }
                }
            },
        },
        403: {
            "description": "Forbidden – requires owner or editor role",
            "content": {
                "application/json": {
                    "example": {"detail": {"code": "FORBIDDEN", "message": "Requires project role"}}
                }
            },
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            },
        },
    },
)
def update_project(
        id: int,
        project_data: ProjectCreate,
        service: ProjectService = Depends(get_project_service)
):
    project = service.update_project(id, project_data)
    return ResponseBase(code=200, message="Project updated successfully", data=project)


@router.delete(
    "/{id}",
    dependencies=[Depends(get_current_user),
                  Depends(require_project_role(ProjectRole.owner))],
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete a project",
    description="Delete a project by id. Requires project owner role.",
    responses={
        204: {"description": "Project deleted successfully"},
        403: {
            "description": "Forbidden – requires owner role",
            "content": {
                "application/json": {
                    "example": {"detail": {"code": "FORBIDDEN", "message": "Requires project role ['owner']"}}
                }
            },
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            },
        },
    },
)
def delete_project(id: int, service: ProjectService = Depends(get_project_service)):
    service.delete_project(id)


@router.get(
    "/user/{user_id}",
    dependencies=[Depends(get_current_user)],
    status_code=HTTPStatus.OK,
    response_model=ResponseBase[List[ProjectRead]],
    summary="List projects by user",
    description="List projects owned by or associated with a particular user.",
    responses={
        200: {
            "description": "Projects retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Projects retrieved successfully",
                        "data": [
                            {
                                "id": 1,
                                "name": "Membership Project",
                                "description": "Project for membership tests",
                                "owner_id": 1,
                            }
                        ],
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
def get_projects_by_user(
    user_id: int,
    skip: int = Query(default=0, ge=0, description="Items to skip for pagination"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum projects to return"),
    service: ProjectService = Depends(get_project_service),
):
    project = service.get_project_by_user(user_id, skip=skip, limit=limit)
    return ResponseBase(code=200, message="Projects retrieved successfully", data=project)


@router.post(
    "/{id}/members",
    dependencies=[Depends(get_current_user), Depends(require_project_membership_admin)],
    response_model=ResponseBase[ProjectMemberRead],
    status_code=HTTPStatus.CREATED,
    summary="Add member to project",
    description=(
        "Add a member to a project with a specific project role.\n\n"
        "Requires project owner or system admin."
    ),
    responses={
        201: {
            "description": "Member added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 201,
                        "message": "Member added successfully",
                        "data": {
                            "project_id": 1,
                            "user_id": 2,
                            "role": "viewer",
                        },
                    }
                }
            },
        },
        403: {
            "description": "Forbidden – caller cannot manage members",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have permission to manage members for this project"}
                }
            },
        },
        404: {
            "description": "Project or user not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            },
        },
    },
)
def add_project_member(
        id: int,
        member_in: ProjectMemberAdd,
        service: ProjectService = Depends(get_project_service),
):
    member = service.add_member(id, member_in.user_id, member_in.role)
    return ResponseBase(code=201, message="Member added successfully", data=member)


@router.patch(
    "/{id}/members/{user_id}",
    dependencies=[Depends(get_current_user), Depends(require_project_membership_admin)],
    response_model=ResponseBase[ProjectMemberRead],
    summary="Change project member role",
    description="Change the role of an existing project member.",
    responses={
        200: {
            "description": "Member role updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Member role updated successfully",
                        "data": {
                            "project_id": 1,
                            "user_id": 2,
                            "role": "editor",
                        },
                    }
                }
            },
        },
        403: {
            "description": "Forbidden – caller cannot manage members",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have permission to manage members for this project"}
                }
            },
        },
        404: {
            "description": "Project member not found",
            "content": {
                "application/json": {
                    "example": {"detail": "project_member 1:2 not found"}
                }
            },
        },
    },
)
def change_project_member_role(
        id: int,
        user_id: int,
        member_in: ProjectMemberUpdate,
        service: ProjectService = Depends(get_project_service),
):
    member = service.change_member_role(id, user_id, member_in.role)
    return ResponseBase(code=200, message="Member role updated successfully", data=member)


@router.delete(
    "/{id}/members/{user_id}",
    dependencies=[Depends(get_current_user), Depends(require_project_membership_admin)],
    status_code=HTTPStatus.NO_CONTENT,
    summary="Remove project member",
    description="Remove a member from a project. Requires project owner or system admin.",
    responses={
        204: {"description": "Member removed successfully"},
        403: {
            "description": "Forbidden – caller cannot manage members",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have permission to manage members for this project"}
                }
            },
        },
        404: {
            "description": "Project member not found",
            "content": {
                "application/json": {
                    "example": {"detail": "project_member 1:2 not found"}
                }
            },
        },
    },
)
def remove_project_member(
        id: int,
        user_id: int,
        service: ProjectService = Depends(get_project_service),
):
    service.remove_member(id, user_id)
