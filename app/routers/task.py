from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.task_repository import TaskRepository
from app.routers.users import get_current_user, require_project_role
from app.schemas.UserSchema import TaskBase, TaskCreate, TaskRead, ProjectRole
from app.schemas.response import ResponseBase
from app.services.task.implementation import TaskService

router = APIRouter(
    tags=["tasks"],
    prefix="/task"
)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    service = TaskService()
    service.set_repository(TaskRepository(db))
    return service


@router.get("/{id}", response_model=ResponseBase[TaskBase], dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor, ProjectRole.viewer))])
def get_task(id: int, service: TaskService = Depends(get_task_service)):
    task = service.get_task(id)
    return ResponseBase(code=200, message="Task retrieved successfully", data=task)


@router.get("", response_model=ResponseBase[List[TaskBase]], dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor, ProjectRole.viewer))])
def get_all_tasks(skip: int = Query(0, ge=0),
                  limit: int = Query(10, ge=1, le=100), service: TaskService = Depends(get_task_service),
                  ):
    tasks = service.get_all_tasks(skip, limit)
    return ResponseBase(code=200, message="Tasks retrieved successfully", data=tasks)


@router.post("", response_model=ResponseBase[TaskRead], dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor))])
def create_task(task: TaskCreate, service: TaskService = Depends(get_task_service)):
    task = service.create_task(task)
    return ResponseBase(code=201, message="Task created successfully", data=task)


@router.delete("/{id}", response_model=ResponseBase[TaskBase], dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor))])
def delete_task(id: int, service: TaskService = Depends(get_task_service)):
    task = service.delete_task(id)
    return ResponseBase(code=200, message="Task deleted successfully", data=task)


@router.put("/{id}", response_model=ResponseBase[TaskBase], dependencies=[Depends(get_current_user), Depends(
    require_project_role(ProjectRole.owner, ProjectRole.editor))])
def update_task(id: int, task: TaskBase, service: TaskService = Depends(get_task_service),
                ):
    task = service.update_task(id, task)
    return ResponseBase(code=200, message="Task updated successfully", data=task)


@router.get("/user/{id}", status_code=200, response_model=ResponseBase[List[TaskBase]],dependencies=[Depends(get_current_user)])
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
