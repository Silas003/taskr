from fastapi import FastAPI
from app.database import engine, Base
import os

from app.routers.v1 import v1_router
from dotenv import load_dotenv,find_dotenv
from fastapi.openapi.utils import get_openapi

# Load the environment variables from the .env file
load_dotenv(find_dotenv())
app = FastAPI(title="Taskr API")
app.include_router(v1_router,prefix="/api")

def custom_openapi():
    if app.openapi_schema:
        app.openapi_schema = None  # force regeneration every time
    return get_openapi(
        title="Taskr API",
        version="1.0.0",
        routes=app.routes,
    )

app.openapi = custom_openapi


if not os.getenv("SKIP_CREATE_ALL"):
    Base.metadata.create_all(bind=engine)



