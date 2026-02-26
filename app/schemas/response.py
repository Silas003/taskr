from typing import TypeVar, Generic

from pydantic import BaseModel

T = TypeVar("T")
class ResponseBase(BaseModel,Generic[T]):
    code: int
    message: str
    data: T | None