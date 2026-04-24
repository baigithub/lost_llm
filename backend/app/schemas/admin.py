from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, Field


class UserAdminUpdate(BaseModel):
    status: Optional[int] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    email: Optional[str] = None


class UserCreateAdmin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(default="123456", min_length=6, max_length=100)
    phone: Optional[str] = None
    real_name: Optional[str] = None
    email: Optional[str] = None
    role_ids: List[int] = Field(default_factory=list)


class UserRolesBody(BaseModel):
    role_ids: List[int] = Field(default_factory=list)


class RoleCreate(BaseModel):
    name: str = Field(..., max_length=50)
    code: str = Field(..., max_length=50)
    sort: int = 0
    remark: Optional[str] = None
    status: int = 1


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    sort: Optional[int] = None
    remark: Optional[str] = None
    status: Optional[int] = None


class MenuCreate(BaseModel):
    parent_id: int = 0
    name: str = Field(..., max_length=50)
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    permission: Optional[str] = None
    sort: int = 0
    visible: int = 1


class MenuUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    permission: Optional[str] = None
    sort: Optional[int] = None
    visible: Optional[int] = None


class CategoryCreate(BaseModel):
    category_name: str = Field(..., max_length=50)
    parent_id: Optional[int] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class RoleMenusBody(BaseModel):
    menu_ids: List[int] = Field(default_factory=list)


class HomeListPageSizeBody(BaseModel):
    page_size: int = Field(..., ge=5, le=100)
