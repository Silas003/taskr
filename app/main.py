import os

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.database import engine, Base
from app.routers.v1 import v1_router
from app.schemas.response import ResponseBase

load_dotenv(find_dotenv())
app = FastAPI(title="Taskr API")

ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")
ALLOWED_METHODS = os.getenv("CORS_ALLOWED_METHODS", "*")
ALLOWED_HEADERS = os.getenv("CORS_ALLOWED_HEADERS", "*")
ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()] if ALLOWED_ORIGINS != "*" else ["*"]
methods = [m.strip() for m in ALLOWED_METHODS.split(",") if m.strip()] if ALLOWED_METHODS != "*" else ["*"]
headers = [h.strip() for h in ALLOWED_HEADERS.split(",") if h.strip()] if ALLOWED_HEADERS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=methods,
    allow_headers=headers,
)

app.include_router(v1_router, prefix="/api", tags=["v1"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseBase(
            code=exc.status_code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            data=None,
        ).dict(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ResponseBase(
            code=500,
            message="An unexpected error occurred",
            data=None,
        ).dict(),
    )


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
