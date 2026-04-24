from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoginLog(Base):
    __tablename__ = "login_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), index=True)
    ip: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(Integer)  # 1 成功 0 失败
    msg: Mapped[Optional[str]] = mapped_column(String(255))
    login_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(50))
    module: Mapped[Optional[str]] = mapped_column(String(50))
    operation: Mapped[Optional[str]] = mapped_column(String(50))
    url: Mapped[Optional[str]] = mapped_column(String(200))
    method: Mapped[Optional[str]] = mapped_column(String(10))
    params: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[Optional[str]] = mapped_column(String(50))
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    ip: Mapped[Optional[str]] = mapped_column(String(50))
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ExceptionLog(Base):
    __tablename__ = "exception_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    username: Mapped[Optional[str]] = mapped_column(String(50))
    exception_type: Mapped[Optional[str]] = mapped_column(String(200))
    message: Mapped[Optional[str]] = mapped_column(Text)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(200))
    params: Mapped[Optional[str]] = mapped_column(Text)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
