from fastapi import FastAPI
from app.database import engine, Base
import os

from app.routers import users as users_router
from dotenv import load_dotenv,find_dotenv

# Load the environment variables from the .env file
load_dotenv(find_dotenv())
app = FastAPI(title="Taskr API")

if not os.getenv("SKIP_CREATE_ALL"):
    Base.metadata.create_all(bind=engine)

app.include_router(users_router.router)


@app.get("/")
def root():
    return {"message": "Taskr API is running"}