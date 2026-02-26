from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.schemas.response import ResponseBase

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseBase(
            code=exc.status_code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            data=None
        ).dict()
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ResponseBase(
            code=500,
            message="An unexpected error occurred",
            data=None
        ).dict()
    )