from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.deps import get_current_user
from app.models.item import Claim, ClaimStatus, Item
from app.models.log import LoginLog
from app.models.user import Role, User, UserRole
from app.schemas.common import ok
from app.schemas.user import TokenOut, UserLogin, UserOut, UserRegister

router = APIRouter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="学号/用户名已存在")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        phone=data.phone,
        real_name=data.real_name,
        status=1,
    )
    db.add(user)
    db.flush()
    role = db.query(Role).filter(Role.code == "user").first()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return ok({"id": user.id})


@router.post("/login", response_model=TokenOut)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username, User.is_deleted == 0).first()
    ok_login = bool(user and verify_password(data.password, user.password_hash) and user.status == 1)
    db.add(
        LoginLog(
            username=data.username,
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent", "")[:250],
            status=1 if ok_login else 0,
            msg=None if ok_login else "用户名或密码错误",
            login_time=datetime.utcnow(),
        )
    )
    db.commit()
    if not ok_login:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id, extra={"username": user.username})
    return TokenOut(access_token=token)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))


def _menus_payload(user: User, db: Session):
    from app.models.menu import Menu, RoleMenu

    role_ids = [r.id for r in user.roles]
    if not role_ids:
        return []
    menu_ids = (
        db.query(RoleMenu.menu_id)
        .filter(RoleMenu.role_id.in_(role_ids))
        .distinct()
        .all()
    )
    mids = [m[0] for m in menu_ids]
    if not mids:
        return []
    rows = db.query(Menu).filter(Menu.id.in_(mids), Menu.visible == 1).order_by(Menu.sort).all()
    return [
        {
            "id": m.id,
            "parent_id": m.parent_id,
            "name": m.name,
            "path": m.path,
            "icon": m.icon,
            "permission": m.permission,
            "sort": m.sort,
        }
        for m in rows
    ]


@router.get("/menus")
def my_menus_get(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(_menus_payload(user, db))


@router.post("/menus")
def my_menus(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(_menus_payload(user, db))


@router.get("/notifications/summary")
def notifications_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    codes = {r.code for r in user.roles}
    if codes & {"claim_reviewer", "admin", "super_admin"}:
        n = db.query(func.count(Claim.id)).filter(Claim.status == ClaimStatus.pending).scalar() or 0
        return ok({"pending_claim_reviews": int(n)})
    ids = [row[0] for row in db.query(Item.id).filter(Item.user_id == user.id).all()]
    if not ids:
        return ok({"pending_claim_reviews": 0})
    n = (
        db.query(func.count(Claim.id))
        .filter(Claim.item_id.in_(ids), Claim.status == ClaimStatus.pending)
        .scalar()
        or 0
    )
    return ok({"pending_claim_reviews": int(n)})
