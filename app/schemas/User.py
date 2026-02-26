from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.UserSchema import SystemRole


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    role:SystemRole = SystemRole.member

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)

class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    role:SystemRole

    class Config:
        orm_mode = True

# Auth response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProjectBase(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class TaskStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class TaskBase(BaseModel):
    id: int
    title: str
    description: Optional[str]
    project_id: int
    status: TaskStatusEnum
    due_date: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True

