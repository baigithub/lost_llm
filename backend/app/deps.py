from __future__ import annotations
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    db: Session = Depends(get_db),
    cred: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    if not cred or not cred.credentials:
        return None
    payload = decode_token(cred.credentials)
    if not payload or "sub" not in payload:
        return None
    user = db.query(User).filter(User.id == int(payload["sub"]), User.is_deleted == 0).first()
    if not user or user.status != 1:
        return None
    return user


def get_current_user(
    db: Session = Depends(get_db),
    cred: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    user = get_current_user_optional(db, cred)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或令牌无效")
    return user


def require_roles(*codes: str):
    def _inner(user: User = Depends(get_current_user)) -> User:
        user_codes = {r.code for r in user.roles}
        if "super_admin" in user_codes:
            return user
        if not user_codes.intersection(set(codes)):
            raise HTTPException(status_code=403, detail="权限不足")
        return user

    return _inner
