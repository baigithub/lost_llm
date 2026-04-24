from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.deps import get_current_user, get_current_user_optional
from app.models.dictionary import DictionaryItem
from app.models.item import Category, Claim, ClaimStatus, Item, ItemImage, ItemStatus, ItemType
from app.models.user import User
from app.schemas.common import ok
from app.schemas.item import ClaimCreate, ItemCreate
from app.services.site_settings import get_home_list_page_size
from app.utils.phone import mask_phone
from app.utils.privacy import mask_location_public, redact_description

router = APIRouter()


def _public_status_filter():
    return Item.status.in_([ItemStatus.pending, ItemStatus.matched])


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


def _image_mask_mode(*, is_self: bool, item_type: ItemType) -> str:
    if is_self:
        return "none"
    if item_type == ItemType.found:
        return "partial"
    return "full"


@router.get("/meta/categories")
def list_categories_public(db: Session = Depends(get_db)):
    rows = db.query(Category).order_by(Category.sort_order, Category.id).all()
    return ok([{"id": c.id, "name": c.category_name, "parent_id": c.parent_id} for c in rows])


@router.get("/meta/home-list-page-size")
def home_list_page_size_meta(db: Session = Depends(get_db)):
    return ok({"page_size": get_home_list_page_size(db)})


@router.get("")
def list_items(
    db: Session = Depends(get_db),
    current: Optional[User] = Depends(get_current_user_optional),
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    q = db.query(Item).options(selectinload(Item.images), selectinload(Item.publisher))
    if not current:
        q = q.filter(_public_status_filter())
    else:
        # 未登录仅看公开；登录用户默认同公开（管理端另做）
        q = q.filter(
            or_(
                _public_status_filter(),
                Item.user_id == current.id,
            )
        )
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(or_(Item.title.like(kw), Item.description.like(kw)))
    if category_id:
        q = q.filter(Item.category_id == category_id)
    if type in ("lost", "found"):
        q = q.filter(Item.type == ItemType(type))
    if status in ("pending", "matched", "claimed", "expired"):
        q = q.filter(Item.status == ItemStatus(status))
    total = q.count()
    rows: List[Item] = (
        q.order_by(Item.publish_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    )
    status_labels = _item_status_label_map(db)
    items_out = []
    for it in rows:
        phone = it.publisher.phone if it.publisher else None
        is_self = bool(current and current.id == it.user_id)
        if is_self:
            desc = (
                it.description[:120] + "..."
                if it.description and len(it.description) > 120
                else it.description
            )
            loc = it.location
            privacy_masked = False
        else:
            desc = redact_description(it.description, max_len=90)
            loc = mask_location_public(it.location)
            privacy_masked = True
        image_mask_mode = _image_mask_mode(is_self=is_self, item_type=it.type)
        items_out.append(
            {
                "id": it.id,
                "title": it.title,
                "description": desc,
                "category_id": it.category_id,
                "type": it.type.value,
                "status": status_labels.get(it.status.value, _item_status_zh(it.status)),
                "status_code": it.status.value,
                "location": loc,
                "contact_info": it.contact_info or mask_phone(phone),
                "occur_time": it.occur_time,
                "publish_time": it.publish_time,
                "views": it.views,
                "publisher_phone": mask_phone(phone),
                "is_owner": is_self,
                "privacy_masked": privacy_masked,
                "image_mask_mode": image_mask_mode,
                "images": [{"image_url": im.image_url, "is_primary": im.is_primary} for im in it.images],
            }
        )
    return ok({"total": total, "items": items_out})


@router.get("/{item_id}")
def item_detail(
    item_id: int,
    db: Session = Depends(get_db),
    current: Optional[User] = Depends(get_current_user_optional),
):
    it = (
        db.query(Item)
        .options(selectinload(Item.images), selectinload(Item.publisher))
        .filter(Item.id == item_id)
        .first()
    )
    if not it:
        raise HTTPException(status_code=404, detail="物品不存在")
    is_owner = current and current.id == it.user_id
    if it.status == ItemStatus.offline and not is_owner:
        raise HTTPException(status_code=404, detail="物品不存在或已下架")
    if it.status in (ItemStatus.claimed, ItemStatus.expired) and not is_owner:
        raise HTTPException(status_code=404, detail="物品不存在或已下架")
    it.views = (it.views or 0) + 1
    db.commit()
    phone = it.publisher.phone if it.publisher else None
    if is_owner:
        description = it.description
        location = it.location
        privacy_masked = False
    else:
        description = redact_description(it.description, max_len=200)
        location = mask_location_public(it.location)
        privacy_masked = True
    image_mask_mode = _image_mask_mode(is_self=bool(is_owner), item_type=it.type)
    data = {
        "id": it.id,
        "title": it.title,
        "description": description,
        "category_id": it.category_id,
        "type": it.type.value,
        "status": _item_status_label_map(db).get(it.status.value, _item_status_zh(it.status)),
        "status_code": it.status.value,
        "location": location,
        "contact_info": it.contact_info or mask_phone(phone),
        "occur_time": it.occur_time,
        "publish_time": it.publish_time,
        "views": it.views,
        "publisher_id": it.user_id,
        "publisher_phone_masked": mask_phone(phone),
        "privacy_masked": privacy_masked,
        "image_mask_mode": image_mask_mode,
        "images": [{"image_url": im.image_url, "is_primary": im.is_primary} for im in it.images],
    }
    return ok(data)


@router.post("")
def create_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    item = Item(
        title=body.title,
        description=body.description,
        category_id=body.category_id,
        type=body.type,
        status=ItemStatus.pending,
        location=body.location,
        contact_info=body.contact_info,
        occur_time=body.occur_time,
        user_id=current.id,
        publish_time=datetime.utcnow(),
    )
    db.add(item)
    db.flush()
    for i, url in enumerate(body.image_urls):
        db.add(
            ItemImage(
                item_id=item.id,
                image_url=url,
                is_primary=1 if i == 0 else 0,
                sort_order=i,
            )
        )
    db.commit()
    db.refresh(item)
    return ok({"id": item.id})


@router.post("/{item_id}/claims")
def create_claim(
    item_id: int,
    body: ClaimCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="物品不存在")
    if it.user_id == current.id:
        raise HTTPException(status_code=400, detail="不能认领自己的物品")
    if it.status == ItemStatus.offline:
        raise HTTPException(status_code=400, detail="该物品已下架")
    if it.status in (ItemStatus.claimed, ItemStatus.expired):
        raise HTTPException(status_code=400, detail="该物品已结束招领")
    exists = (
        db.query(Claim)
        .filter(Claim.item_id == item_id, Claim.claimant_id == current.id, Claim.status == ClaimStatus.pending)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="已有待审核的认领申请")
    c = Claim(
        item_id=item_id,
        claimant_id=current.id,
        verification_proof=body.verification_proof,
        contact_info=body.contact_info,
        status=ClaimStatus.pending,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id})


@router.post("/{item_id}/offline")
def offline_item(
    item_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="物品不存在")
    if it.user_id != current.id:
        raise HTTPException(status_code=403, detail="仅发布者可下架")
    if it.status == ItemStatus.offline:
        raise HTTPException(status_code=400, detail="已是下架状态")
    if it.status not in (ItemStatus.pending, ItemStatus.matched):
        raise HTTPException(status_code=400, detail="当前状态不可下架")
    it.status = ItemStatus.offline
    db.commit()
    return ok({})


@router.post("/{item_id}/online")
def online_item(
    item_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="物品不存在")
    if it.user_id != current.id:
        raise HTTPException(status_code=403, detail="仅发布者可上架")
    if it.status != ItemStatus.offline:
        raise HTTPException(status_code=400, detail="仅下架状态可重新上架")
    it.status = ItemStatus.pending
    db.commit()
    return ok({})


@router.get("/claims/my")
def my_claims(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    status_labels = _item_status_label_map(db)
    rows = (
        db.query(Claim)
        .options(selectinload(Claim.item), selectinload(Claim.reviewer))
        .filter(Claim.claimant_id == current.id)
        .order_by(Claim.create_time.desc())
        .all()
    )
    return ok(
        [
            {
                "id": c.id,
                "item_id": c.item_id,
                "item_title": c.item.title if c.item else None,
                "status": c.status.value,
                "verification_proof": c.verification_proof,
                "contact_info": c.contact_info,
                "reviewer_id": c.reviewer_id,
                "reviewer_username": c.reviewer.username if c.reviewer else None,
                "reject_reason": c.reject_reason,
                "item_status_code": c.item.status.value if c.item else None,
                "item_status": status_labels.get(c.item.status.value, _item_status_zh(c.item.status)) if c.item else None,
                "reviewed_at": c.reviewed_at,
                "create_time": c.create_time,
            }
            for c in rows
        ]
    )


@router.get("/published/my")
def my_published(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    rows = db.query(Item).filter(Item.user_id == current.id).order_by(Item.publish_time.desc()).all()
    status_labels = _item_status_label_map(db)
    return ok(
        [
            {
                "id": it.id,
                "title": it.title,
                "status": status_labels.get(it.status.value, _item_status_zh(it.status)),
                "status_code": it.status.value,
                "type": it.type.value,
                "contact_info": it.contact_info or (current.phone if hasattr(current, "phone") else None),
                "publish_time": it.publish_time,
            }
            for it in rows
        ]
    )


@router.get("/{item_id}/claims")
def list_claims_for_item(
    item_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it or it.user_id != current.id:
        raise HTTPException(status_code=403, detail="仅发布者可查看")
    rows = db.query(Claim).filter(Claim.item_id == item_id).order_by(Claim.create_time.desc()).all()
    return ok(
        [
            {
                "id": c.id,
                "claimant_id": c.claimant_id,
                "verification_proof": c.verification_proof,
                "status": c.status.value,
                "create_time": c.create_time,
            }
            for c in rows
        ]
    )


@router.post("/claims/{claim_id}/approve")
def approve_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = db.query(Claim).filter(Claim.id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="申请不存在")
    it = db.query(Item).filter(Item.id == c.item_id).first()
    if not it or it.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    if it.status == ItemStatus.offline:
        raise HTTPException(status_code=400, detail="物品已下架")
    c.status = ClaimStatus.approved
    c.reviewer_id = current.id
    c.reviewed_at = datetime.utcnow()
    c.reject_reason = None
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
def reject_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = db.query(Claim).filter(Claim.id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="申请不存在")
    it = db.query(Item).filter(Item.id == c.item_id).first()
    if not it or it.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    if it.status == ItemStatus.offline:
        raise HTTPException(status_code=400, detail="物品已下架")
    c.status = ClaimStatus.rejected
    c.reviewer_id = current.id
    c.reviewed_at = datetime.utcnow()
    if not c.reject_reason:
        c.reject_reason = "审核未通过"
    db.commit()
    return ok({})
