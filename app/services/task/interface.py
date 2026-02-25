
from abc import  ABC,abstractmethod

class ITaskService(ABC):
    @abstractmethod
    def create_task(self,task_data):
        """Create a new task."""
        pass

    @abstractmethod
    def get_task(self, task_id):
        """Retrieve a task by its ID."""
        pass

    @abstractmethod
    def update_task(self, task_id, task_data):
        """Update an existing task."""
        pass

    @abstractmethod
    def delete_task(self, task_id):
        """Delete a task by its ID."""
        pass

    @abstractmethod
    def get_all_tasks(self,limit:int,offset:int):
        """List all tasks."""
        pass

    @abstractmethod
    def get_task_by_user(self,user_id):
        """List all tasks by user."""
        pass

    @abstractmethod
    def get_task_by_project(self,project_id):
        """List all tasks by project."""
        pass