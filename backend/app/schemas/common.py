from __future__ import annotations
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "ok"
    data: Optional[T] = None


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 200, "message": message, "data": data}


def err(code: int, message: str) -> dict[str, Any]:
    return {"code": code, "message": message, "data": None}
