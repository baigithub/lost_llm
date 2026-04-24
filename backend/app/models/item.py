from __future__ import annotations
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ItemType(str, PyEnum):
    lost = "lost"
    found = "found"


class ItemStatus(str, PyEnum):
    pending = "pending"
    matched = "matched"
    claimed = "claimed"
    expired = "expired"
    offline = "offline"  # 已下架：前台列表与详情对非发布者不可见


class ClaimStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    items: Mapped[List["Item"]] = relationship("Item", back_populates="category")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    type: Mapped[ItemType] = mapped_column(Enum(ItemType), nullable=False)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), default=ItemStatus.pending)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    contact_info: Mapped[Optional[str]] = mapped_column(String(200))
    occur_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    sensitive_info_hash: Mapped[Optional[str]] = mapped_column(String(255))

    publisher: Mapped["User"] = relationship("User", back_populates="items")
    category: Mapped[Optional[Category]] = relationship("Category", back_populates="items")
    images: Mapped[List["ItemImage"]] = relationship(
        "ItemImage",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="ItemImage.sort_order",
    )
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="item", cascade="all, delete-orphan")


class ItemImage(Base):
    __tablename__ = "item_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    item: Mapped[Item] = relationship("Item", back_populates="images")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    claimant_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    verification_proof: Mapped[Optional[str]] = mapped_column(Text)
    contact_info: Mapped[Optional[str]] = mapped_column(String(200))
    reject_reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), default=ClaimStatus.pending)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    item: Mapped[Item] = relationship("Item", back_populates="claims")
    claimant: Mapped["User"] = relationship("User", foreign_keys=[claimant_id], back_populates="claims")
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewer_id])