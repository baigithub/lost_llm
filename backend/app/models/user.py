from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.item import Claim, Item
    from app.models.menu import RoleMenu


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[Optional[str]] = mapped_column(String(50))
    student_id: Mapped[Optional[str]] = mapped_column(String(20))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(Integer, default=1)  # 0 禁用 1 启用
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)

    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )
    items: Mapped[List["Item"]] = relationship("Item", back_populates="publisher")
    claims: Mapped[List["Claim"]] = relationship("Claim", foreign_keys="Claim.claimant_id", back_populates="claimant")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)
    remark: Mapped[Optional[str]] = mapped_column(String(255))

    users: Mapped[List[User]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )
    menu_links: Mapped[List["RoleMenu"]] = relationship(
        "RoleMenu",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
