from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DictionaryItem(Base):
    __tablename__ = "dictionary_items"
    __table_args__ = (UniqueConstraint("dict_type", "code", name="uq_dict_type_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dict_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)  # 1 启用 0 禁用
    remark: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
