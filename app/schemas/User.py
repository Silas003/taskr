from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    id:int
    username:str
    email:EmailStr
    full_name:str
    created_at:str
    updated_at:str

class UserCreate(UserBase):
    password:str

class UserUpdate(UserBase):
    password:str

class ProjectBase(BaseModel):
    id:int
    name:str
    description:Optional[str]
    owner_id:int
    created_at:str

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class TaskStatusEnum(Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class TaskBase(BaseModel):
    id:int
    title:str
    description:Optional[str]
    project_id:int
    status:TaskStatusEnum
    due_date:Optional[str]
    created_at:str

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    pass