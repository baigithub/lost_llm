from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import Role


class Menu(Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(Integer, default=0, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[Optional[str]] = mapped_column(String(100))
    component: Mapped[Optional[str]] = mapped_column(String(100))
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    permission: Mapped[Optional[str]] = mapped_column(String(100))
    sort: Mapped[int] = mapped_column(Integer, default=0)
    visible: Mapped[int] = mapped_column(Integer, default=1)

    role_links: Mapped[List["RoleMenu"]] = relationship("RoleMenu", back_populates="menu")


class RoleMenu(Base):
    __tablename__ = "role_menus"
    __table_args__ = (UniqueConstraint("role_id", "menu_id", name="uq_role_menu"),)

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    menu_id: Mapped[int] = mapped_column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), primary_key=True)

    role: Mapped["Role"] = relationship("Role", back_populates="menu_links")
    menu: Mapped[Menu] = relationship("Menu", back_populates="role_links")
