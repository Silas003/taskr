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
    tags=["tasks"],
    prefix="/task"
)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    service = TaskService()
    service.set_repository(TaskRepository(db))
    return service


@router.get("/{id}", response_model=ResponseBase[TaskRead], dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor, ProjectRole.viewer))])
def get_task(id: int, service: TaskService = Depends(get_task_service)):
    task = service.get_task(id)
    return ResponseBase(code=200, message="Task retrieved successfully", data=task)


@router.get("", response_model=ResponseBase[List[TaskRead]], dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor, ProjectRole.viewer))])
def get_all_tasks(skip: int = Query(0, ge=0),
                  limit: int = Query(10, ge=1, le=100),
                  service: TaskService = Depends(get_task_service)):
    tasks = service.get_all_tasks(limit=limit, offset=skip)
    return ResponseBase(code=200, message="Tasks retrieved successfully", data=tasks)


@router.post("", response_model=ResponseBase[TaskRead], status_code=201,
             dependencies=[Depends(get_current_user), Depends(
                 require_project_role(ProjectRole.owner, ProjectRole.editor))])
def create_task(task: TaskCreate, service: TaskService = Depends(get_task_service)):
    task = service.create_task(task)
    return ResponseBase(code=201, message="Task created successfully", data=task)


@router.delete("/{id}", status_code=204, dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor))])
def delete_task(id: int, service: TaskService = Depends(get_task_service)):
    return service.delete_task(id)


@router.put("/{id}", response_model=ResponseBase[TaskBase])
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

    # Owners and editors: full update
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


@router.get("/user/{id}", status_code=200, response_model=ResponseBase[List[TaskBase]],
            dependencies=[Depends(get_current_user)])
def get_task_by_user_id(id: int, service: TaskService = Depends(get_task_service)):
    task = service.get_task_by_user(id)
    return ResponseBase(
        code=200,
        message="User tasks retrieved successfully",
        data=task
    )


@router.get("/project/{id}", status_code=200, response_model=ResponseBase[List[TaskBase]],
            dependencies=[Depends(get_current_user)])
def get_task_by_project_id(id: int, service: TaskService = Depends(get_task_service)):
    task = service.get_task_by_project(id)
    return ResponseBase(
        code=200,
        message="Project tasks retrieved successfully",
        data=task
    )
