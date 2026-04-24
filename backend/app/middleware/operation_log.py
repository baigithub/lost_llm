from __future__ import annotations
import time
from typing import Callable

from fastapi import Request, Response
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.log import OperationLog


def _op_type(method: str) -> str:
    return {
        "GET": "query",
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }.get(method.upper(), method.lower())


class OperationLogMiddleware(BaseHTTPMiddleware):
    """记录管理端 API 调用（不含 multipart 上传）。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if not path.startswith("/api/v1/admin"):
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = getattr(response, "status_code", 200)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            _write_op_log(request, path, duration_ms, 500, "failed")
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        result = "success" if status < 400 else "failed"
        _write_op_log(request, path, duration_ms, status, result)
        return response


def _write_op_log(request: Request, path: str, duration_ms: int, status: int, result: str) -> None:
    user_id = None
    username = None
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        payload = decode_token(auth.split(" ", 1)[1].strip())
        if payload and "sub" in payload:
            try:
                user_id = int(payload["sub"])
            except (TypeError, ValueError):
                user_id = None
            username = payload.get("username")
    params = str(request.query_params) if request.query_params else ""
    db: Session = SessionLocal()
    try:
        db.add(
            OperationLog(
                user_id=user_id,
                username=username,
                module="admin",
                operation=_op_type(request.method),
                url=path[:200],
                method=request.method,
                params=params[:4000],
                result=result if status < 400 else "failed",
                duration=duration_ms,
                ip=request.client.host if request.client else None,
            )
        )
        db.commit()
    finally:
        db.close()
