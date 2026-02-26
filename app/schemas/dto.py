from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SystemRole(str, Enum):
    admin = "admin"
    member = "member"
    viewer = "viewer"


class ProjectRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"



class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    role: SystemRole = SystemRole.member


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    role: SystemRole

    class Config:
        from_attributes = True



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"



class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime


class ProjectRead(ProjectCreate):
    id: int

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectMemberAdd(BaseModel):
    user_id: int
    role: ProjectRole


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberRead(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: ProjectRole

    class Config:
        from_attributes = True


class TaskStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class TaskBase(BaseModel):
    title: str
    assigned_to: Optional[int] = None
    description: Optional[str] = None
    project_id: int
    status: TaskStatusEnum
    due_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: int


class TaskUpdate(TaskBase):
    pass
