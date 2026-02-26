from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.task_repository import TaskRepository
from app.routers.v1.project import get_project_service
from app.routers.v1.users import get_current_user, require_project_role
from app.schemas.dto import TaskBase, TaskCreate, TaskRead, ProjectRole, TaskStatusEnum
from app.schemas.response import ResponseBase
from app.services.project.implementation import ProjectService
from app.services.task.implementation import TaskService

router = APIRouter(
    tags=["Tasks"],
    prefix="/task"
)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    service = TaskService()
    service.set_repository(TaskRepository(db))
    return service


@router.get(
    "/{id}",
    response_model=ResponseBase[TaskRead],
    dependencies=[Depends(get_current_user), Depends(require_project_role(ProjectRole.owner, ProjectRole.editor, ProjectRole.viewer))],
    summary="Get task by id",
    description="Retrieve a single task by its id (requires project membership).",
    responses={
        200: {
            "description": "Task retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Task retrieved successfully",
                        "data": {
                            "id": 1,
                            "title": "Set up CI",
                            "description": "Configure CI pipeline",
                            "project_id": 1,
                            "assigned_to": 2,
                            "status": "pending",
                        },
                    }
                }
            },
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            },
        },
        403: {
            "description": "Forbidden – user not a project member",
            "content": {
                "application/json": {
                    "example": {"detail": {"code": "FORBIDDEN", "message": "Requires project role"}}
                }
            },
        },
    },
)
def get_task(id: int, service: TaskService = Depends(get_task_service)):
    task = service.get_task(id)
    return ResponseBase(code=200, message="Task retrieved successfully", data=task)


@router.get(
    "",
    response_model=ResponseBase[List[TaskRead]],
    dependencies=[Depends(get_current_user), Depends(require_project_role(ProjectRole.owner, ProjectRole.editor, ProjectRole.viewer))],
    summary="List tasks",
    description="List tasks in projects where the user has at least viewer access.",
    responses={
        200: {
            "description": "Tasks retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Tasks retrieved successfully",
                        "data": [
                            {
                                "id": 1,
                                "title": "Set up CI",
                                "description": "Configure CI pipeline",
                                "project_id": 1,
                                "assigned_to": 2,
                                "status": "pending",
                            }
                        ],
                    }
                }
            },
        },
        403: {
            "description": "Forbidden – user not a member of any relevant projects",
            "content": {
                "application/json": {
                    "example": {"detail": {"code": "FORBIDDEN", "message": "Requires project role"}}
                }
            },
        },
    },
)
def get_all_tasks(skip: int = Query(0, ge=0, description="Items to skip for pagination"),
                  limit: int = Query(10, ge=1, le=100, description="Maximum tasks to return"),
                  service: TaskService = Depends(get_task_service)):
    tasks = service.get_all_tasks(limit=limit, offset=skip)
    return ResponseBase(code=200, message="Tasks retrieved successfully", data=tasks)


@router.post(
    "",
    response_model=ResponseBase[TaskRead],
    status_code=201,
    dependencies=[Depends(get_current_user), Depends(require_project_role(ProjectRole.owner, ProjectRole.editor))],
    summary="Create task",
    description="Create a new task in a project. Requires owner or editor role on the project.",
    responses={
        201: {
            "description": "Task created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 201,
                        "message": "Task created successfully",
                        "data": {
                            "id": 1,
                            "title": "New Task",
                            "description": "Task description",
                            "project_id": 1,
                            "assigned_to": None,
                            "status": "pending",
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
    },
)
def create_task(task: TaskCreate, service: TaskService = Depends(get_task_service)):
    task = service.create_task(task)
    return ResponseBase(code=201, message="Task created successfully", data=task)


@router.delete(
    "/{id}",
    status_code=204,
    dependencies=[Depends(get_current_user), Depends(require_project_role(ProjectRole.owner, ProjectRole.editor))],
    summary="Delete task",
    description="Delete a task by id. Requires owner or editor role on the project.",
    responses={
        204: {"description": "Task deleted successfully"},
        403: {
            "description": "Forbidden – requires owner or editor role",
            "content": {
                "application/json": {
                    "example": {"detail": {"code": "FORBIDDEN", "message": "Requires project role"}}
                }
            },
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            },
        },
    },
)
def delete_task(id: int, service: TaskService = Depends(get_task_service)):
    return service.delete_task(id)


@router.put(
    "/{id}",
    response_model=ResponseBase[TaskBase],
    summary="Update task",
    description=(
        "Update an existing task.\n\n"
        "- Owners/editors can update all fields.\n"
        "- Viewers assigned to the task can update status only."
    ),
    responses={
        200: {
            "description": "Task updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Task updated successfully",
                        "data": {
                            "id": 1,
                            "title": "Updated Task",
                            "description": "Updated description",
                            "project_id": 1,
                            "assigned_to": 2,
                            "status": "in_progress",
                        },
                    }
                }
            },
        },
        403: {
            "description": "Forbidden – user cannot update this task",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have permission to update this task"}
                }
            },
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            },
        },
    },
)
def update_task(
        id: int,
        task: TaskBase,
        current_user=Depends(get_current_user),
        service: TaskService = Depends(get_task_service),
        project_service: ProjectService = Depends(get_project_service)
):
    existing = service.get_task(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    membership = project_service.get_project_member(existing.project_id, current_user.id)
    project_role = membership.role if membership else None

    if project_role in (ProjectRole.owner, ProjectRole.editor):
        updated = service.update_task(id, task)
        return ResponseBase(code=200, message="Task updated successfully", data=updated)

    if project_role == ProjectRole.viewer and existing.assigned_to == current_user.id:
        task_status_val = task.status.value if hasattr(task.status, "value") else str(task.status)
        if task.status is None or task_status_val == existing.status:
            raise HTTPException(status_code=403, detail="No permitted fields to update")
        partial = TaskBase(
            title=existing.title,
            assigned_to=existing.assigned_to,
            description=existing.description,
            project_id=existing.project_id,
            status=TaskStatusEnum(task.status),
            due_date=existing.due_date,
            created_at=existing.created_at,
        )
        updated = service.update_task(id, partial)
        return ResponseBase(code=200, message="Task status updated successfully", data=updated)

    raise HTTPException(status_code=403, detail="You do not have permission to update this task")


@router.get(
    "/user/{id}",
    status_code=200,
    response_model=ResponseBase[List[TaskBase]],
    dependencies=[Depends(get_current_user)],
    summary="List tasks by user",
    description="List tasks assigned to a given user.",
    responses={
        200: {
            "description": "User tasks retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "User tasks retrieved successfully",
                        "data": [
                            {
                                "id": 1,
                                "title": "User Task",
                                "description": "Task for user",
                                "project_id": 1,
                                "status": "pending",
                                "due_date": None,
                                "created_at": "2024-01-01T00:00:00Z",
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
def get_task_by_user_id(
    id: int,
    skip: int = Query(0, ge=0, description="Items to skip for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Maximum tasks to return"),
    service: TaskService = Depends(get_task_service),
):
    task = service.get_task_by_user(id, skip=skip, limit=limit)
    return ResponseBase(
        code=200,
        message="User tasks retrieved successfully",
        data=task,
    )


@router.get(
    "/project/{id}",
    status_code=200,
    response_model=ResponseBase[List[TaskBase]],
    dependencies=[Depends(get_current_user)],
    summary="List tasks by project",
    description="List all tasks that belong to a given project.",
    responses={
        200: {
            "description": "Project tasks retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "message": "Project tasks retrieved successfully",
                        "data": [
                            {
                                "id": 1,
                                "title": "Project Task",
                                "description": "Task for project",
                                "project_id": 1,
                                "status": "pending",
                                "due_date": None,
                                "created_at": "2024-01-01T00:00:00Z",
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
def get_task_by_project_id(
    id: int,
    skip: int = Query(0, ge=0, description="Items to skip for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Maximum tasks to return"),
    service: TaskService = Depends(get_task_service),
):
    task = service.get_task_by_project(id, skip=skip, limit=limit)
    return ResponseBase(
        code=200,
        message="Project tasks retrieved successfully",
        data=task,
    )
