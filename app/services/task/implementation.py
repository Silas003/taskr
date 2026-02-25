from app.services.task.interface import ITaskService


class TaskService(ITaskService):
    """TaskService implements the ITaskService interface for task management."""

    def __init__(self):
        self.repository = None

    def set_repository(self, repository):
        """Set the repository for this service."""
        self.repository = repository

    def create_task(self, db, task_in):
        """Create a new task."""
        return self.repository.create(db, task_in)

    def get_task(self, db, task_id):
        """Get a task by ID."""
        return self.repository.get(db, task_id)

    def update_task(self, db, task_id, task_in):
        """Update an existing task."""
        return self.repository.update(db, task_id, task_in)

    def delete_task(self, db, task_id):
        """Delete a task by ID."""
        return self.repository.delete(db, task_id)