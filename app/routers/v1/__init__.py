from fastapi import APIRouter

from app.routers.v1 import users, project, task, health

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(users.router)
v1_router.include_router(project.router)
v1_router.include_router(task.router)
v1_router.include_router(health.router)
