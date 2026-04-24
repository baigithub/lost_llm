from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None
    real_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleBrief(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[RoleBrief] = []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class MenuOut(BaseModel):
    id: int
    parent_id: int
    name: str
    path: Optional[str] = None
    icon: Optional[str] = None
    permission: Optional[str] = None
    sort: int = 0

    class Config:
        from_attributes = True
