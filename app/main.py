from fastapi import FastAPI
from app.database import engine, Base
import os

from app.routers.v1 import v1_router
from dotenv import load_dotenv,find_dotenv

# Load the environment variables from the .env file
load_dotenv(find_dotenv())
app = FastAPI(title="Taskr API")


if not os.getenv("SKIP_CREATE_ALL"):
    Base.metadata.create_all(bind=engine)

app.include_router(v1_router,prefix="/api")

