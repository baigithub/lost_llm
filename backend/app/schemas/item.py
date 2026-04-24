from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.item import ClaimStatus, ItemStatus, ItemType


class ItemCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    type: ItemType
    location: Optional[str] = None
    contact_info: Optional[str] = None
    occur_time: Optional[datetime] = None
    image_urls: List[str] = Field(..., min_length=1, description="至少一张图片 URL")


class ItemListQuery(BaseModel):
    keyword: Optional[str] = None
    category_id: Optional[int] = None
    type: Optional[ItemType] = None
    status: Optional[ItemStatus] = None
    page: int = 1
    page_size: int = 10


class ItemImageOut(BaseModel):
    image_url: str
    is_primary: int = 0

    class Config:
        from_attributes = True


class ItemOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    type: str
    status: str
    location: Optional[str] = None
    occur_time: Optional[datetime] = None
    publish_time: Optional[datetime] = None
    views: int = 0
    publisher_phone_masked: Optional[str] = None
    images: List[ItemImageOut] = []

    class Config:
        from_attributes = True


class ItemDetailOut(ItemOut):
    publisher_id: int
    description_full: Optional[str] = None


class ClaimCreate(BaseModel):
    verification_proof: str = Field(..., min_length=5)
    contact_info: Optional[str] = None


class ClaimOut(BaseModel):
    id: int
    item_id: int
    claimant_id: int
    verification_proof: Optional[str] = None
    status: str
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True
