from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    id:int
    username:str
    email:EmailStr
    full_name:str
    created_at:datetime
    updated_at:datetime

class UserCreate(UserBase):
    password:str

class UserUpdate(UserBase):
    password:str

class ProjectBase(BaseModel):
    name:str
    description:Optional[str]
    owner_id:int
    created_at:datetime

class ProjectCreate(ProjectBase):
    pass

class ProjectRead(ProjectBase):
    id:int

class ProjectUpdate(ProjectBase):
    pass

class TaskStatusEnum(Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class TaskBase(BaseModel):
    title:str
    assigned_to:Optional[int] = None
    description:Optional[str] = None
    project_id:int
    status:TaskStatusEnum
    due_date:Optional[datetime] = None
    created_at:datetime

    class Config:
        orm_mode = True

class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    id:int

class TaskUpdate(TaskBase):
    pass

class SystemRole(str, Enum):
    admin = "admin"
    member = "member"
    viewer = "viewer"

class ProjectRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"
