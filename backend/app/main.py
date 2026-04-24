from __future__ import annotations
import os
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from app.api.v1 import admin, auth, items, recognition
from app.middleware.operation_log import OperationLogMiddleware
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import *  # noqa: F401,F403
from app.models.log import ExceptionLog
from app.scripts.seed import seed_if_empty
from app.services.site_settings import ensure_default_system_settings

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(OperationLogMiddleware)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(items.router, prefix=f"{settings.API_V1_PREFIX}/items", tags=["items"])
app.include_router(recognition.router, prefix=f"{settings.API_V1_PREFIX}/recognition", tags=["recognition"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["admin"])


@app.on_event("startup")
def _startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # lightweight runtime migration for claims review fields
        db.execute(text("ALTER TABLE claims ADD COLUMN reject_reason TEXT"))
    except Exception:
        pass
    try:
        db.execute(text("ALTER TABLE claims ADD COLUMN reviewer_id INTEGER NULL"))
    except Exception:
        pass
    try:
        db.execute(text("ALTER TABLE claims ADD COLUMN reviewed_at DATETIME NULL"))
    except Exception:
        pass
    try:
        db.execute(text("ALTER TABLE items ADD COLUMN contact_info VARCHAR(200) NULL"))
    except Exception:
        pass
    try:
        db.execute(
            text(
                "ALTER TABLE items "
                "MODIFY COLUMN status ENUM('pending','matched','claimed','expired','offline') "
                "NOT NULL DEFAULT 'pending'"
            )
        )
    except Exception:
        pass
    try:
        seed_if_empty(db)
        ensure_default_system_settings(db)
        db.commit()
    finally:
        db.close()


@app.exception_handler(Exception)
async def global_exc(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": "参数校验失败", "data": exc.errors()},
        )
    if isinstance(exc, HTTPException):
        detail = exc.detail
        msg = detail if isinstance(detail, str) else str(detail)
        return JSONResponse(status_code=exc.status_code, content={"code": exc.status_code, "message": msg, "data": None})
    if isinstance(exc, OperationalError):
        return JSONResponse(
            status_code=503,
            content={
                "code": 503,
                "message": "数据库连接失败，请确认 MySQL 已启动，并检查 backend/.env 中的 MYSQL_HOST、MYSQL_PORT 等配置",
                "data": None,
            },
        )
    try:
        db = SessionLocal()
        try:
            db.add(
                ExceptionLog(
                    user_id=None,
                    username=None,
                    exception_type=type(exc).__name__,
                    message=str(exc)[:2000],
                    stack_trace=traceback.format_exc()[:8000],
                    url=str(request.url.path),
                    params=None,
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception:
        pass
    return JSONResponse(status_code=500, content={"code": 500, "message": "服务器内部错误", "data": None})


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok"}
