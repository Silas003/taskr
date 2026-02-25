from app.models import Task
from app.repositories.task_repository import TaskRepository,ITaskRepository
from app.schemas.UserSchema import TaskCreate
from app.services.task.interface import ITaskService


class TaskService(ITaskService):
    """TaskService implements the ITaskService interface for task management."""

    def __init__(self,repository: TaskRepository = None):
        self.repository = repository

    def set_repository(self, repository:ITaskRepository):
        """Set the repository for this service."""
        self.repository = repository

    def create_task(self, task_in:TaskCreate):
        """Create a new task."""
        task = Task(
            title=task_in.title,
            description=task_in.description,
            assigned_to=task_in.assigned_to,
            status=task_in.status.value,
            due_date=task_in.due_date,
            project_id=task_in.project_id,
            created_at=task_in.created_at
        )
        return self.repository.save( task)

    def get_task(self,  task_id):
        """Get a task by ID."""
        return self.repository.get_by_id(task_id)

    def update_task(self,task_id, task_in):
        """Update an existing task."""
        return self.repository.update( task_id, task_in)

    def delete_task(self, task_id):
        """Delete a task by ID."""
        return self.repository.delete(task_id)

    def get_all_tasks(self,limit:int,offset:int):
        return self.repository.find_all(limit,offset)

    def get_task_by_user(self,user_id):
        return self.repository.get_task_by_user(user_id)

    def get_task_by_project(self,project_id):
        return self.repository.get_task_by_project(project_id)