from abc import ABC,abstractmethod
from sqlalchemy.orm import Session

from app.models import Project
from app.models.Task import Task
from app.models.User import User
from typing import List, Optional


class ITaskRepository(ABC):
    @abstractmethod
    def save(self, task_data):
        pass
    @abstractmethod
    def get_by_id(self, task_id):
        pass

    @abstractmethod
    def update(self, task_id, task_data):
        pass

    @abstractmethod
    def delete(self, task_id):
        pass
    @abstractmethod
    def find_all(self,limit:int,offset:int):
        pass


class TaskRepository(ITaskRepository):
    def __init__(self, db:Session):
        self.db = db

    def save(self, task:Task)->Task:
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    def get_by_id(self, task_id)->Task:
        return self.db.get(Task,task_id)

    def update(self, task_id, task_data):
        task = self.get_by_id(task_id)
        if not task:
            return None
        for key, value in task_data.items():
            setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task_id)->bool:
        task = self.get_by_id(task_id)
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True

    def find_all(self,skip:int,limit:int)-> List[Task]:
        self.db.query(Task).offset(skip).limit(limit).all()


    def get_task_by_user(self,user_id)->List[Task]:
        user = self.db.get(User,user_id)
        if user is not None:
            return user.tasks
        return []

    def get_task_by_project(self,project_id)->List[Task]:
        project = self.db.get(Project,project_id)
        if project is not None:
            return project.tasks
        return []

