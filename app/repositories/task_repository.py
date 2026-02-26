from abc import ABC,abstractmethod
from sqlalchemy.orm import Session

from app.exceptions.CustomExceptions import EntityNotFound
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
    def find_all(self, limit: int, offset: int):
        pass

    @abstractmethod
    def get_task_by_user(self, user_id: int, skip: int = 0, limit: int = 10):
        pass

    @abstractmethod
    def get_task_by_project(self, project_id: int, skip: int = 0, limit: int = 10):
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
        try:
            task = self.get_by_id(task_id)
            if not task:
                return None
            for key, value in task_data.items():
                setattr(task, key, value)
            self.db.commit()
            self.db.refresh(task)
            return task
        except Exception:
            self.db.rollback()
            raise

    def delete(self, task_id)->bool:
        db_task = self.get_by_id(task_id)
        if not db_task:
            return False
        self.db.delete(task_id)
        self.db.commit()
        return True

    def find_all(self, limit: int, offset: int) -> List[Task]:
        return self.db.query(Task).offset(offset).limit(limit).all()

    def get_task_by_user(self, user_id: int, skip: int = 0, limit: int = 10) -> List[Task]:
        return (
            self.db.query(Task)
            .filter(Task.assigned_to == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_task_by_project(self, project_id: int, skip: int = 0, limit: int = 10) -> List[Task]:
        return (
            self.db.query(Task)
            .filter(Task.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
