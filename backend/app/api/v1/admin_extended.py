from __future__ import annotations
import csv
import io
from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import hash_password
from app.deps import require_roles
from app.models.item import Category, Claim, ClaimStatus, Item, ItemStatus, ItemType
from app.models.dictionary import DictionaryItem
from app.models.log import ExceptionLog, LoginLog, OperationLog
from app.models.menu import Menu, RoleMenu
from app.models.user import Role, User, UserRole
from app.schemas.admin import (
    CategoryCreate,
    CategoryUpdate,
    HomeListPageSizeBody,
    MenuCreate,
    MenuUpdate,
    RoleCreate,
    RoleMenusBody,
    RoleUpdate,
    UserAdminUpdate,
    UserCreateAdmin,
    UserRolesBody,
)
from app.services.site_settings import get_home_list_page_size, set_home_list_page_size
from app.schemas.common import ok
from app.utils.operation_menu import make_menu_name_resolver
from app.utils.privacy import mask_middle_30

router = APIRouter()
_admin = require_roles("admin", "super_admin")
_claim_staff = require_roles("claim_reviewer", "admin", "super_admin")


def _item_status_zh(s: ItemStatus) -> str:
    mapping = {
        ItemStatus.pending: "招领中",
        ItemStatus.matched: "匹配中",
        ItemStatus.claimed: "已认领",
        ItemStatus.expired: "已过期",
        ItemStatus.offline: "已下架",
    }
    return mapping.get(s, s.value if hasattr(s, "value") else str(s))


def _item_status_label_map(db: Session) -> dict[str, str]:
    rows = (
        db.query(DictionaryItem)
        .filter(DictionaryItem.dict_type == "item_status", DictionaryItem.status == 1)
        .order_by(DictionaryItem.sort_order, DictionaryItem.id)
        .all()
    )
    out: dict[str, str] = {}
    for r in rows:
        out[r.code] = r.label
    return out


def _ensure_claim_reviewer_role(db: Session) -> None:
    role = db.query(Role).filter(Role.code == "claim_reviewer").first()
    if role:
        return
    db.add(
        Role(
            name="物品招领审核员",
            code="claim_reviewer",
            sort=5,
            status=1,
            remark="专门审核招领物品的认领申请，审核通过后流程结束",
        )
    )
    db.commit()


class DictItemBody(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=100)
    sort_order: int = 0
    status: int = 1
    remark: Optional[str] = None


class ClaimRejectBody(BaseModel):
    reject_reason: str = Field(..., min_length=2, max_length=500)


def _csv_response(rows: List[List[Any]], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf)
    for r in rows:
        writer.writerow(r)
    data = "\ufeff" + buf.getvalue()
    return StreamingResponse(
        iter([data.encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------- 看板 ----------
@router.get("/dashboard")
def dashboard(
    _: User = Depends(_claim_staff),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).filter(User.is_deleted == 0).scalar() or 0
    total_items = db.query(func.count(Item.id)).scalar() or 0
    pending_items = db.query(func.count(Item.id)).filter(Item.status == ItemStatus.pending).scalar() or 0
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    today_end = today_start + timedelta(days=1)
    approved_claims_today = (
        db.query(func.count(Claim.id))
        .filter(
            Claim.status == ClaimStatus.approved,
            Claim.reviewed_at >= today_start,
            Claim.reviewed_at < today_end,
        )
        .scalar()
        or 0
    )
    login_today = (
        db.query(func.count(LoginLog.id))
        .filter(LoginLog.login_time >= today_start, LoginLog.login_time < today_end, LoginLog.status == 1)
        .scalar()
        or 0
    )
    return ok(
        {
            "total_users": int(total_users),
            "total_items": int(total_items),
            "pending_items": int(pending_items),
            "approved_claims_today": int(approved_claims_today),
            "login_success_today": int(login_today),
        }
    )


@router.get("/dashboard/charts")
def dashboard_charts(
    _: User = Depends(_claim_staff),
    db: Session = Depends(get_db),
):
    # 1) 发布物品按分类
    pub_cat_rows = (
        db.query(Category.category_name, func.count(Item.id))
        .join(Item, Item.category_id == Category.id)
        .group_by(Category.category_name)
        .order_by(func.count(Item.id).desc())
        .all()
    )
    publish_by_category = [{"name": n or "未分类", "value": int(v or 0)} for n, v in pub_cat_rows]

    # 2) 认领申请按分类（基于物品分类）
    claim_cat_rows = (
        db.query(Category.category_name, func.count(Claim.id))
        .join(Item, Item.category_id == Category.id)
        .join(Claim, Claim.item_id == Item.id)
        .group_by(Category.category_name)
        .order_by(func.count(Claim.id).desc())
        .all()
    )
    claims_by_category = [{"name": n or "未分类", "value": int(v or 0)} for n, v in claim_cat_rows]

    # 3) 发布物品按状态占比
    status_rows = db.query(Item.status, func.count(Item.id)).group_by(Item.status).all()
    status_map = {
        ItemStatus.pending: "招领中",
        ItemStatus.matched: "匹配中",
        ItemStatus.claimed: "已认领",
        ItemStatus.expired: "已过期",
        ItemStatus.offline: "已下架",
    }
    publish_by_status = [
        {"name": status_map.get(s, str(s.value if hasattr(s, "value") else s)), "value": int(v or 0)}
        for s, v in status_rows
    ]

    # 4) 发布物品按类型占比
    type_rows = db.query(Item.type, func.count(Item.id)).group_by(Item.type).all()
    type_map = {
        ItemType.lost: "寻物",
        ItemType.found: "招领",
    }
    publish_by_type = [
        {"name": type_map.get(t, str(t.value if hasattr(t, "value") else t)), "value": int(v or 0)}
        for t, v in type_rows
    ]

    # 5) 柱状图：按发布日期统计发布数量 Top5
    pub_date_rows = (
        db.query(func.date(Item.publish_time), func.count(Item.id))
        .group_by(func.date(Item.publish_time))
        .order_by(func.count(Item.id).desc())
        .limit(5)
        .all()
    )
    publish_top5_dates = [{"date": str(d), "value": int(v or 0)} for d, v in pub_date_rows]

    # 6) 折线图：按日期统计认领申请数量 Top5
    claim_date_rows = (
        db.query(func.date(Claim.create_time), func.count(Claim.id))
        .group_by(func.date(Claim.create_time))
        .order_by(func.count(Claim.id).desc())
        .limit(5)
        .all()
    )
    claims_top5_dates = [{"date": str(d), "value": int(v or 0)} for d, v in claim_date_rows]

    # 7) 雷达图：按分类展示发布物品 + 认领申请总量（Top5）
    claim_map = {x["name"]: int(x["value"]) for x in claims_by_category}
    combined = []
    for x in publish_by_category:
        name = x["name"]
        combined.append({"name": name, "value": int(x["value"]) + int(claim_map.get(name, 0))})
    combined.sort(key=lambda z: z["value"], reverse=True)
    radar_top = combined[:5]
    max_v = max([x["value"] for x in radar_top], default=1)
    radar = {
        "indicators": [{"name": x["name"], "max": max_v} for x in radar_top],
        "values": [x["value"] for x in radar_top],
    }

    return ok(
        {
            "publish_by_category": publish_by_category,
            "claims_by_category": claims_by_category,
            "publish_by_status": publish_by_status,
            "publish_by_type": publish_by_type,
            "publish_top5_dates": publish_top5_dates,
            "claims_top5_dates": claims_top5_dates,
            "publish_category_radar": radar,
        }
    )


# ---------- 认领审核（审核员 / 管理员） ----------
@router.get("/claims/pending")
def admin_pending_claims(
    _: User = Depends(_claim_staff),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
):
    status_labels = _item_status_label_map(db)
    q = db.query(Claim).filter(Claim.status == ClaimStatus.pending)
    total = q.count()
    rows = (
        q.options(
            selectinload(Claim.item).selectinload(Item.publisher),
            selectinload(Claim.claimant),
        )
        .order_by(Claim.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items_out = []
    for c in rows:
        it = c.item
        pub = it.publisher if it else None
        cl = c.claimant
        items_out.append(
            {
                "id": c.id,
                "item_id": c.item_id,
                "item_title": it.title if it else "",
                "publisher_id": it.user_id if it else None,
                "publisher_username": pub.username if pub else None,
                "claimant_id": c.claimant_id,
                "claimant_username": cl.username if cl else None,
                "verification_proof": c.verification_proof,
                "contact_info": c.contact_info,
                "item_status_code": it.status.value if it else None,
                "item_status": status_labels.get(it.status.value, _item_status_zh(it.status)) if it else None,
                "create_time": c.create_time,
            }
        )
    return ok({"total": total, "items": items_out})


@router.get("/claims/reviewed/mine")
def my_reviewed_claims(
    current: User = Depends(_claim_staff),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
):
    status_labels = _item_status_label_map(db)
    q = db.query(Claim).filter(Claim.status.in_([ClaimStatus.approved, ClaimStatus.rejected]), Claim.reviewer_id == current.id)
    total = q.count()
    rows = (
        q.options(
            selectinload(Claim.item).selectinload(Item.publisher),
            selectinload(Claim.claimant),
            selectinload(Claim.reviewer),
        )
        .order_by(Claim.reviewed_at.desc(), Claim.update_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items_out = []
    for c in rows:
        it = c.item
        pub = it.publisher if it else None
        cl = c.claimant
        rv = c.reviewer
        items_out.append(
            {
                "id": c.id,
                "item_id": c.item_id,
                "item_title": it.title if it else "",
                "publisher_username": pub.username if pub else None,
                "claimant_username": cl.username if cl else None,
                "verification_proof": c.verification_proof,
                "contact_info": c.contact_info,
                "status": c.status.value,
                "reject_reason": c.reject_reason,
                "item_status_code": it.status.value if it else None,
                "item_status": status_labels.get(it.status.value, _item_status_zh(it.status)) if it else None,
                "reviewed_at": c.reviewed_at,
                "reviewer_username": rv.username if rv else None,
                "create_time": c.create_time,
            }
        )
    return ok({"total": total, "items": items_out})


@router.get("/claims/{claim_id}/detail")
def claim_detail_for_review(
    claim_id: int,
    _: User = Depends(_claim_staff),
    db: Session = Depends(get_db),
):
    c = (
        db.query(Claim)
        .options(
            selectinload(Claim.item).selectinload(Item.images),
            selectinload(Claim.item).selectinload(Item.publisher),
            selectinload(Claim.claimant),
            selectinload(Claim.reviewer),
        )
        .filter(Claim.id == claim_id)
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="申请不存在")
    it = c.item
    if not it:
        raise HTTPException(status_code=404, detail="物品不存在")
    return ok(
        {
            "claim": {
                "id": c.id,
                "status": c.status.value,
                "verification_proof": c.verification_proof,
                "contact_info": c.contact_info,
                "reject_reason": c.reject_reason,
                "create_time": c.create_time,
                "reviewed_at": c.reviewed_at,
                "claimant_username": c.claimant.username if c.claimant else None,
                "reviewer_username": c.reviewer.username if c.reviewer else None,
            },
            "item": {
                "id": it.id,
                "title": it.title,
                "description": it.description,
                "location": it.location,
                "type": it.type.value,
                "status": it.status.value,
                "publisher_username": it.publisher.username if it.publisher else None,
                "images": [{"image_url": im.image_url, "is_primary": im.is_primary} for im in it.images],
            },
        }
    )


@router.post("/claims/{claim_id}/approve")
def admin_approve_claim(
    claim_id: int,
    current: User = Depends(_claim_staff),
    db: Session = Depends(get_db),
):
    c = db.query(Claim).filter(Claim.id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="申请不存在")
    if c.status != ClaimStatus.pending:
        raise HTTPException(status_code=400, detail="当前非待审核状态")
    it = db.query(Item).filter(Item.id == c.item_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="物品不存在")
    if it.status == ItemStatus.offline:
        raise HTTPException(status_code=400, detail="物品已下架")
    c.status = ClaimStatus.approved
    c.reject_reason = None
    c.reviewer_id = current.id
    c.reviewed_at = datetime.utcnow()
    it.status = ItemStatus.claimed
    db.query(Claim).filter(Claim.item_id == it.id, Claim.id != claim_id).update(
        {
            Claim.status: ClaimStatus.rejected,
            Claim.reject_reason: "该物品已由其他申请认领通过",
            Claim.reviewer_id: current.id,
            Claim.reviewed_at: datetime.utcnow(),
        },
        synchronize_session=False,
    )
    db.commit()
    return ok({"item_id": it.id, "claim_id": c.id})


@router.post("/claims/{claim_id}/reject")
def admin_reject_claim(
    claim_id: int,
    body: ClaimRejectBody,
    current: User = Depends(_claim_staff),
    db: Session = Depends(get_db),
):
    c = db.query(Claim).filter(Claim.id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="申请不存在")
    if c.status != ClaimStatus.pending:
        raise HTTPException(status_code=400, detail="当前非待审核状态")
    it = db.query(Item).filter(Item.id == c.item_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="物品不存在")
    if it.status == ItemStatus.offline:
        raise HTTPException(status_code=400, detail="物品已下架")
    c.status = ClaimStatus.rejected
    c.reject_reason = body.reject_reason.strip()
    c.reviewer_id = current.id
    c.reviewed_at = datetime.utcnow()
    db.commit()
    return ok({})


# ---------- 用户 ----------
@router.get("/users")
def list_users(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    status: Optional[int] = None,
):
    q = db.query(User).filter(User.is_deleted == 0)
    if username:
        q = q.filter(User.username.like(f"%{username}%"))
    if status is not None:
        q = q.filter(User.status == status)
    total = q.count()
    rows = q.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ok(
        {
            "total": total,
            "items": [
                {
                    "id": u.id,
                    "username": u.username,
                    "real_name": u.real_name,
                    "phone": u.phone,
                    "email": u.email,
                    "status": u.status,
                    "roles": [{"id": r.id, "code": r.code, "name": r.name} for r in u.roles],
                }
                for u in rows
            ],
        }
    )


@router.post("/users")
def create_user(
    body: UserCreateAdmin,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, detail="用户名已存在")
    u = User(
        username=body.username,
        password_hash=hash_password(body.password),
        phone=body.phone,
        real_name=body.real_name,
        email=body.email,
        status=1,
    )
    db.add(u)
    db.flush()
    for rid in body.role_ids:
        if db.query(Role).filter(Role.id == rid).first():
            db.add(UserRole(user_id=u.id, role_id=rid))
    db.commit()
    return ok({"id": u.id})


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserAdminUpdate,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id, User.is_deleted == 0).first()
    if not u:
        raise HTTPException(404, detail="用户不存在")
    if body.status is not None:
        u.status = body.status
    if body.phone is not None:
        u.phone = body.phone
    if body.real_name is not None:
        u.real_name = body.real_name
    if body.email is not None:
        u.email = body.email
    db.commit()
    return ok({})


@router.post("/users/{user_id}/roles")
def set_user_roles(
    user_id: int,
    body: UserRolesBody,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, detail="用户不存在")
    db.query(UserRole).filter(UserRole.user_id == user_id).delete(synchronize_session=False)
    for rid in body.role_ids:
        if db.query(Role).filter(Role.id == rid).first():
            db.add(UserRole(user_id=user_id, role_id=rid))
    db.commit()
    return ok({})


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, detail="用户不存在")
    u.password_hash = hash_password("123456")
    db.commit()
    return ok({})


# ---------- 角色 ----------
@router.get("/roles")
def list_roles(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    _ensure_claim_reviewer_role(db)
    rows = db.query(Role).order_by(Role.sort).all()
    return ok(
        [
            {
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "sort": r.sort,
                "status": r.status,
                "remark": r.remark,
            }
            for r in rows
        ]
    )


@router.post("/roles")
def create_role(
    body: RoleCreate,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    if db.query(Role).filter(or_(Role.code == body.code, Role.name == body.name)).first():
        raise HTTPException(400, detail="角色名或标识已存在")
    r = Role(name=body.name, code=body.code, sort=body.sort, remark=body.remark, status=body.status)
    db.add(r)
    db.commit()
    db.refresh(r)
    return ok({"id": r.id})


@router.put("/roles/{role_id}")
def update_role(
    role_id: int,
    body: RoleUpdate,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    r = db.query(Role).filter(Role.id == role_id).first()
    if not r:
        raise HTTPException(404, detail="角色不存在")
    if r.code == "super_admin" and body.code and body.code != "super_admin":
        raise HTTPException(400, detail="不能修改超级管理员标识")
    if r.code == "claim_reviewer" and body.code and body.code != "claim_reviewer":
        raise HTTPException(400, detail="不能修改招领审核员标识")
    if body.name is not None:
        r.name = body.name
    if body.code is not None:
        r.code = body.code
    if body.sort is not None:
        r.sort = body.sort
    if body.remark is not None:
        r.remark = body.remark
    if body.status is not None:
        r.status = body.status
    db.commit()
    return ok({})


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    r = db.query(Role).filter(Role.id == role_id).first()
    if not r:
        raise HTTPException(404, detail="角色不存在")
    if r.code in ("super_admin", "user", "claim_reviewer"):
        raise HTTPException(400, detail="系统预置角色不可删除")
    db.query(UserRole).filter(UserRole.role_id == role_id).delete(synchronize_session=False)
    db.query(RoleMenu).filter(RoleMenu.role_id == role_id).delete(synchronize_session=False)
    db.delete(r)
    db.commit()
    return ok({})


@router.get("/roles/{role_id}/menus")
def get_role_menus(
    role_id: int,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    if not db.query(Role).filter(Role.id == role_id).first():
        raise HTTPException(404, detail="角色不存在")
    mids = [m[0] for m in db.query(RoleMenu.menu_id).filter(RoleMenu.role_id == role_id).all()]
    return ok({"menu_ids": mids})


@router.put("/roles/{role_id}/menus")
def set_role_menus(
    role_id: int,
    body: RoleMenusBody,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    if not db.query(Role).filter(Role.id == role_id).first():
        raise HTTPException(404, detail="角色不存在")
    db.query(RoleMenu).filter(RoleMenu.role_id == role_id).delete(synchronize_session=False)
    for mid in body.menu_ids:
        if db.query(Menu).filter(Menu.id == mid).first():
            db.add(RoleMenu(role_id=role_id, menu_id=mid))
    db.commit()
    return ok({})


# ---------- 菜单 ----------
def _menu_tree(db: Session, parent_id: int = 0) -> List[dict[str, Any]]:
    rows = db.query(Menu).filter(Menu.parent_id == parent_id).order_by(Menu.sort).all()
    out: List[dict[str, Any]] = []
    for m in rows:
        out.append(
            {
                "id": m.id,
                "parent_id": m.parent_id,
                "name": m.name,
                "path": m.path,
                "component": m.component,
                "icon": m.icon,
                "permission": m.permission,
                "sort": m.sort,
                "visible": m.visible,
                "children": _menu_tree(db, m.id),
            }
        )
    return out


@router.get("/menus/tree")
def menu_tree(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    return ok(_menu_tree(db, 0))


@router.post("/menus")
def create_menu(
    body: MenuCreate,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    m = Menu(
        parent_id=body.parent_id,
        name=body.name,
        path=body.path,
        component=body.component,
        icon=body.icon,
        permission=body.permission,
        sort=body.sort,
        visible=body.visible,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return ok({"id": m.id})


@router.put("/menus/{menu_id}")
def update_menu(
    menu_id: int,
    body: MenuUpdate,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    m = db.query(Menu).filter(Menu.id == menu_id).first()
    if not m:
        raise HTTPException(404, detail="菜单不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(m, k, v)
    db.commit()
    return ok({})


@router.delete("/menus/{menu_id}")
def delete_menu(
    menu_id: int,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    m = db.query(Menu).filter(Menu.id == menu_id).first()
    if not m:
        raise HTTPException(404, detail="菜单不存在")
    if db.query(Menu).filter(Menu.parent_id == menu_id).count() > 0:
        raise HTTPException(400, detail="请先删除子菜单")
    db.query(RoleMenu).filter(RoleMenu.menu_id == menu_id).delete(synchronize_session=False)
    db.delete(m)
    db.commit()
    return ok({})


# ---------- 分类 ----------
@router.get("/dictionary/item-status")
def list_item_status_dict(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DictionaryItem)
        .filter(DictionaryItem.dict_type == "item_status")
        .order_by(DictionaryItem.sort_order, DictionaryItem.id)
        .all()
    )
    data = []
    for r in rows:
        usage_count = db.query(func.count(Item.id)).filter(Item.status == ItemStatus(r.code)).scalar() if r.code in ItemStatus._value2member_map_ else 0
        data.append(
            {
                "id": r.id,
                "code": r.code,
                "label": r.label,
                "sort_order": r.sort_order,
                "status": r.status,
                "remark": r.remark,
                "usage_count": int(usage_count or 0),
            }
        )
    return ok(data)


@router.post("/dictionary/item-status")
def create_item_status_dict(
    body: DictItemBody,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    code = body.code.strip().lower()
    if code not in ItemStatus._value2member_map_:
        raise HTTPException(400, detail="code 必须为 pending/matched/claimed/expired/offline 之一")
    exists = (
        db.query(DictionaryItem)
        .filter(DictionaryItem.dict_type == "item_status", DictionaryItem.code == code)
        .first()
    )
    if exists:
        raise HTTPException(400, detail="字典项 code 已存在")
    db.add(
        DictionaryItem(
            dict_type="item_status",
            code=code,
            label=body.label.strip(),
            sort_order=body.sort_order,
            status=1 if body.status else 0,
            remark=body.remark,
        )
    )
    db.commit()
    return ok({})


@router.put("/dictionary/item-status/{dict_id}")
def update_item_status_dict(
    dict_id: int,
    body: DictItemBody,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    row = db.query(DictionaryItem).filter(DictionaryItem.id == dict_id, DictionaryItem.dict_type == "item_status").first()
    if not row:
        raise HTTPException(404, detail="字典项不存在")
    code = body.code.strip().lower()
    if code not in ItemStatus._value2member_map_:
        raise HTTPException(400, detail="code 必须为 pending/matched/claimed/expired/offline 之一")
    dup = (
        db.query(DictionaryItem)
        .filter(DictionaryItem.dict_type == "item_status", DictionaryItem.code == code, DictionaryItem.id != dict_id)
        .first()
    )
    if dup:
        raise HTTPException(400, detail="字典项 code 已存在")
    row.code = code
    row.label = body.label.strip()
    row.sort_order = body.sort_order
    row.status = 1 if body.status else 0
    row.remark = body.remark
    db.commit()
    return ok({})


@router.delete("/dictionary/item-status/{dict_id}")
def delete_item_status_dict(
    dict_id: int,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    row = db.query(DictionaryItem).filter(DictionaryItem.id == dict_id, DictionaryItem.dict_type == "item_status").first()
    if not row:
        raise HTTPException(404, detail="字典项不存在")
    if row.code in ItemStatus._value2member_map_:
        usage = db.query(func.count(Item.id)).filter(Item.status == ItemStatus(row.code)).scalar() or 0
        if int(usage) > 0:
            raise HTTPException(400, detail="该状态仍有物品在使用，无法删除")
    db.delete(row)
    db.commit()
    return ok({})


# ---------- 分类 ----------
@router.get("/categories")
def list_categories(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(Category).order_by(Category.sort_order, Category.id).all()
    return ok([{"id": c.id, "name": c.category_name, "parent_id": c.parent_id, "sort_order": c.sort_order} for c in rows])


@router.post("/categories")
def create_category(
    body: CategoryCreate,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    c = Category(category_name=body.category_name, parent_id=body.parent_id, sort_order=body.sort_order)
    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id})


@router.put("/categories/{category_id}")
def update_category(
    category_id: int,
    body: CategoryUpdate,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Category).filter(Category.id == category_id).first()
    if not c:
        raise HTTPException(404, detail="分类不存在")
    if body.category_name is not None:
        c.category_name = body.category_name
    if body.parent_id is not None:
        c.parent_id = body.parent_id
    if body.sort_order is not None:
        c.sort_order = body.sort_order
    db.commit()
    return ok({})


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Category).filter(Category.id == category_id).first()
    if not c:
        raise HTTPException(404, detail="分类不存在")
    if db.query(Item).filter(Item.category_id == category_id).count() > 0:
        raise HTTPException(400, detail="该分类下仍有物品，无法删除")
    db.delete(c)
    db.commit()
    return ok({})


# ---------- 分页 / 前台列表 ----------
@router.get("/settings/home-list-page-size")
def admin_get_home_list_page_size(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    return ok({"page_size": get_home_list_page_size(db)})


@router.put("/settings/home-list-page-size")
def admin_put_home_list_page_size(
    body: HomeListPageSizeBody,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    n = set_home_list_page_size(db, body.page_size)
    return ok({"page_size": n})


# ---------- 物品管理 ----------
@router.get("/items")
def admin_items(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
):
    q = db.query(Item).options(selectinload(Item.publisher), selectinload(Item.claims).selectinload(Claim.claimant))
    total = q.count()
    rows = q.order_by(Item.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    status_labels = _item_status_label_map(db)
    return ok(
        {
            "total": total,
            "items": [
                {
                    "id": it.id,
                    "title": it.title,
                    "status": status_labels.get(it.status.value, _item_status_zh(it.status)),
                    "status_code": it.status.value,
                    "type": it.type.value,
                    "user_id": it.user_id,
                    "publisher_username": mask_middle_30(it.publisher.username if it.publisher else None),
                    "reviewer_username": mask_middle_30(
                        next((c.claimant.username for c in it.claims if c.status == ClaimStatus.approved and c.claimant), None)
                    ),
                    "claimer_username": mask_middle_30(
                        next(
                            (
                                c.claimant.username
                                for c in sorted(it.claims, key=lambda x: x.create_time or datetime.min, reverse=True)
                                if c.claimant
                            ),
                            None,
                        )
                    ),
                }
                for it in rows
            ],
        }
    )


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(404, detail="物品不存在")
    db.delete(it)
    db.commit()
    return ok({})


# ---------- 日志 ----------
@router.get("/logs/login")
def login_logs(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    status: Optional[int] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    q = db.query(LoginLog)
    if username:
        q = q.filter(LoginLog.username.like(f"%{username}%"))
    if status is not None:
        q = q.filter(LoginLog.status == status)
    if start:
        q = q.filter(LoginLog.login_time >= start)
    if end:
        q = q.filter(LoginLog.login_time <= end)
    total = q.count()
    rows = q.order_by(LoginLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ok(
        {
            "total": total,
            "items": [
                {
                    "id": r.id,
                    "username": r.username,
                    "ip": r.ip,
                    "user_agent": r.user_agent,
                    "status": r.status,
                    "msg": r.msg,
                    "login_time": r.login_time,
                }
                for r in rows
            ],
        }
    )


@router.get("/logs/login/export")
def login_logs_export(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    username: Optional[str] = None,
    status: Optional[int] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    q = db.query(LoginLog)
    if username:
        q = q.filter(LoginLog.username.like(f"%{username}%"))
    if status is not None:
        q = q.filter(LoginLog.status == status)
    if start:
        q = q.filter(LoginLog.login_time >= start)
    if end:
        q = q.filter(LoginLog.login_time <= end)
    rows = q.order_by(LoginLog.id.desc()).limit(10000).all()
    data = [["id", "username", "ip", "status", "msg", "login_time"]]
    for r in rows:
        data.append([r.id, r.username, r.ip, r.status, r.msg or "", r.login_time])
    return _csv_response(data, "login_logs.csv")


@router.get("/logs/operation")
def operation_logs(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    module: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    q = db.query(OperationLog)
    if username:
        q = q.filter(OperationLog.username.like(f"%{username}%"))
    if module:
        q = q.filter(OperationLog.module == module)
    if start:
        q = q.filter(OperationLog.create_time >= start)
    if end:
        q = q.filter(OperationLog.create_time <= end)
    total = q.count()
    rows = q.order_by(OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    menu_name = make_menu_name_resolver(db)
    return ok(
        {
            "total": total,
            "items": [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "username": r.username,
                    "module": r.module,
                    "operation": r.operation,
                    "menu_name": menu_name(r.url),
                    "url": r.url,
                    "method": r.method,
                    "result": r.result,
                    "duration": r.duration,
                    "create_time": r.create_time,
                }
                for r in rows
            ],
        }
    )


@router.get("/logs/operation/export")
def operation_logs_export(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    username: Optional[str] = None,
    module: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    q = db.query(OperationLog)
    if username:
        q = q.filter(OperationLog.username.like(f"%{username}%"))
    if module:
        q = q.filter(OperationLog.module == module)
    if start:
        q = q.filter(OperationLog.create_time >= start)
    if end:
        q = q.filter(OperationLog.create_time <= end)
    rows = q.order_by(OperationLog.id.desc()).limit(10000).all()
    menu_name = make_menu_name_resolver(db)
    data = [
        [
            "id",
            "username",
            "module",
            "operation",
            "menu_name",
            "url",
            "method",
            "result",
            "duration",
            "create_time",
        ]
    ]
    for r in rows:
        data.append(
            [
                r.id,
                r.username,
                r.module,
                r.operation,
                menu_name(r.url),
                r.url,
                r.method,
                r.result,
                r.duration,
                r.create_time,
            ]
        )
    return _csv_response(data, "operation_logs.csv")


@router.get("/logs/exception")
def exception_logs(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    q = db.query(ExceptionLog)
    if username:
        q = q.filter(ExceptionLog.username.like(f"%{username}%"))
    if start:
        q = q.filter(ExceptionLog.create_time >= start)
    if end:
        q = q.filter(ExceptionLog.create_time <= end)
    total = q.count()
    rows = q.order_by(ExceptionLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ok(
        {
            "total": total,
            "items": [
                {
                    "id": r.id,
                    "username": r.username,
                    "exception_type": r.exception_type,
                    "message": r.message,
                    "url": r.url,
                    "create_time": r.create_time,
                }
                for r in rows
            ],
        }
    )


@router.get("/logs/exception/export")
def exception_logs_export(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
    username: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    q = db.query(ExceptionLog)
    if username:
        q = q.filter(ExceptionLog.username.like(f"%{username}%"))
    if start:
        q = q.filter(ExceptionLog.create_time >= start)
    if end:
        q = q.filter(ExceptionLog.create_time <= end)
    rows = q.order_by(ExceptionLog.id.desc()).limit(5000).all()
    data = [["id", "username", "exception_type", "message", "url", "create_time"]]
    for r in rows:
        data.append([r.id, r.username, r.exception_type, (r.message or "")[:500], r.url, r.create_time])
    return _csv_response(data, "exception_logs.csv")


@router.get("/logs/exception/{log_id}")
def exception_detail(
    log_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_admin),
):
    r = db.query(ExceptionLog).filter(ExceptionLog.id == log_id).first()
    if not r:
        raise HTTPException(404, detail="记录不存在")
    return ok(
        {
            "id": r.id,
            "user_id": r.user_id,
            "username": r.username,
            "exception_type": r.exception_type,
            "message": r.message,
            "stack_trace": r.stack_trace,
            "url": r.url,
            "params": r.params,
            "create_time": r.create_time,
        }
    )
