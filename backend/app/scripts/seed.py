from __future__ import annotations
"""首次启动时写入预置角色、管理员账号与示例分类。"""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.dictionary import DictionaryItem
from app.models.item import Category
from app.models.menu import Menu, RoleMenu
from app.models.user import Role, User, UserRole


def _ensure_role_menu(db: Session, role_id: int, menu_id: int) -> None:
    exists = db.query(RoleMenu).filter(RoleMenu.role_id == role_id, RoleMenu.menu_id == menu_id).first()
    if not exists:
        db.add(RoleMenu(role_id=role_id, menu_id=menu_id))


def seed_if_empty(db: Session) -> None:
    role_defaults = [
        ("普通用户", "user", 10),
        ("物品招领审核员", "claim_reviewer", 5),
        ("管理员", "admin", 20),
        ("超级管理员", "super_admin", 0),
    ]
    for name, code, sort in role_defaults:
        if not db.query(Role).filter(Role.code == code).first():
            db.add(Role(name=name, code=code, sort=sort, status=1))
    db.flush()
    claim_reviewer = db.query(Role).filter(Role.code == "claim_reviewer").first()
    if claim_reviewer:
        claim_reviewer.name = "物品招领审核员"
        claim_reviewer.remark = "专门审核招领物品的认领申请，审核通过后流程结束"

    admin_role = db.query(Role).filter(Role.code == "super_admin").first()
    if admin_role and db.query(User).filter(User.username == "admin").first() is None:
        u = User(
            username="admin",
            password_hash=hash_password("admin123"),
            real_name="系统管理员",
            phone="13800000000",
            status=1,
        )
        db.add(u)
        db.flush()
        if not db.query(UserRole).filter(UserRole.user_id == u.id, UserRole.role_id == admin_role.id).first():
            db.add(UserRole(user_id=u.id, role_id=admin_role.id))

    user_role = db.query(Role).filter(Role.code == "user").first()
    if user_role and db.query(User).filter(User.username == "demo").first() is None:
        u2 = User(
            username="demo",
            password_hash=hash_password("demo123"),
            real_name="演示用户",
            phone="13900000000",
            status=1,
        )
        db.add(u2)
        db.flush()
        if not db.query(UserRole).filter(UserRole.user_id == u2.id, UserRole.role_id == user_role.id).first():
            db.add(UserRole(user_id=u2.id, role_id=user_role.id))

    for name in ("证件卡类", "电子产品", "水杯/水壶", "箱包", "钥匙/小件", "其他"):
        if not db.query(Category).filter(Category.category_name == name).first():
            db.add(Category(category_name=name, parent_id=None, sort_order=0))

    admin_r = db.query(Role).filter(Role.code == "admin").first()
    super_r = db.query(Role).filter(Role.code == "super_admin").first()
    if admin_r and super_r:
        defaults = [
            ("仪表盘", "/admin/dashboard", "Odometer", "admin:dashboard", 1),
            ("用户管理", "/admin/users", "User", "sys:user:list", 2),
            ("物品管理", "/admin/items", "Goods", "item:manage", 3),
        ]
        for name, path, icon, perm, sort in defaults:
            m = db.query(Menu).filter(Menu.path == path).first()
            if m:
                continue
            m = Menu(parent_id=0, name=name, path=path, icon=icon, permission=perm, sort=sort)
            db.add(m)
            db.flush()
            _ensure_role_menu(db, admin_r.id, m.id)
            _ensure_role_menu(db, super_r.id, m.id)

    _ensure_extra_menus(db)
    _ensure_claim_review_menu(db)
    _ensure_claim_reviewer_dashboard_menu(db)
    _ensure_item_status_dictionary(db)
    _ensure_dictionary_submenus(db)
    _ensure_system_management_group(db)


def _ensure_claim_review_menu(db: Session) -> None:
    """管理端「认领审核」菜单，供审核员与管理员使用。"""
    m = db.query(Menu).filter(Menu.path == "/admin/claims").first()
    if not m:
        m = Menu(
            parent_id=0,
            name="认领审核",
            path="/admin/claims",
            icon="Bell",
            permission="claim:review",
            sort=9,
            visible=1,
        )
        db.add(m)
        db.flush()
    for code in ("admin", "super_admin", "claim_reviewer"):
        r = db.query(Role).filter(Role.code == code).first()
        if r:
            _ensure_role_menu(db, r.id, m.id)


def _ensure_claim_reviewer_dashboard_menu(db: Session) -> None:
    """审核员可进入工作台看板（仅分配认领审核菜单时仍需要入口）。"""
    dash = db.query(Menu).filter(Menu.path == "/admin/dashboard").first()
    cr = db.query(Role).filter(Role.code == "claim_reviewer").first()
    if dash and cr:
        _ensure_role_menu(db, cr.id, dash.id)


def _ensure_system_management_group(db: Session) -> None:
    """将用户/角色/菜单/日志归入「系统管理」分组，并为管理员角色关联父菜单。"""
    admin_r = db.query(Role).filter(Role.code == "admin").first()
    super_r = db.query(Role).filter(Role.code == "super_admin").first()
    parent = db.query(Menu).filter(Menu.name == "系统管理", Menu.parent_id == 0).first()
    if not parent:
        parent = Menu(
            parent_id=0,
            name="系统管理",
            path="",
            icon="Setting",
            permission="sys:manage",
            sort=15,
            visible=1,
        )
        db.add(parent)
        db.flush()
    child_paths = [
        "/admin/users",
        "/admin/roles",
        "/admin/menus",
        "/admin/logs",
        "/admin/pagination",
        "/admin/dictionary",
    ]
    for i, p in enumerate(child_paths):
        m = db.query(Menu).filter(Menu.path == p).first()
        if m and m.parent_id != parent.id:
            m.parent_id = parent.id
            m.sort = i + 1
    for role in (admin_r, super_r):
        if role:
            _ensure_role_menu(db, role.id, parent.id)
    _remove_redundant_category_menu(db)


def _remove_redundant_category_menu(db: Session) -> None:
    """清理历史遗留一级菜单「分类管理」，避免与仪表盘/字典功能重复。"""
    targets = db.query(Menu).filter(Menu.parent_id == 0, Menu.name == "分类管理").all()
    for m in targets:
        db.query(RoleMenu).filter(RoleMenu.menu_id == m.id).delete(synchronize_session=False)
        if db.query(Menu).filter(Menu.parent_id == m.id).count() == 0:
            db.delete(m)


def _migrate_categories_menu_to_dictionary(db: Session) -> None:
    """旧版「分类管理」(/admin/categories) 升级为「数据字典管理」(/admin/dictionary)。"""
    old = db.query(Menu).filter(Menu.path == "/admin/categories").first()
    if not old:
        return
    if db.query(Menu).filter(Menu.path == "/admin/dictionary").first():
        db.query(RoleMenu).filter(RoleMenu.menu_id == old.id).delete(synchronize_session=False)
        db.delete(old)
        return
    old.path = "/admin/dictionary"
    old.name = "数据字典管理"
    old.icon = "Collection"
    old.permission = "sys:dict:manage"


def _ensure_extra_menus(db: Session) -> None:
    """为已存在库补充管理端菜单（按 path 去重）。"""
    _migrate_categories_menu_to_dictionary(db)
    admin_r = db.query(Role).filter(Role.code == "admin").first()
    super_r = db.query(Role).filter(Role.code == "super_admin").first()
    defaults = [
        ("/admin/roles", "角色管理", "UserFilled", "sys:role:list", 4),
        ("/admin/menus", "菜单管理", "Menu", "sys:menu:list", 5),
        ("/admin/logs", "日志管理", "Document", "sys:log:list", 6),
        ("/admin/dictionary", "数据字典管理", "Collection", "sys:dict:manage", 7),
        ("/admin/pagination", "分页管理", "Histogram", "sys:pagination:config", 8),
    ]
    for path, name, icon, perm, sort in defaults:
        if db.query(Menu).filter(Menu.path == path).first():
            continue
        m = Menu(parent_id=0, name=name, path=path, icon=icon, permission=perm, sort=sort, visible=1)
        db.add(m)
        db.flush()
        if admin_r:
            _ensure_role_menu(db, admin_r.id, m.id)
        if super_r:
            _ensure_role_menu(db, super_r.id, m.id)


def _ensure_item_status_dictionary(db: Session) -> None:
    """预置物品状态字典，供「数据字典管理-物品状态」维护。"""
    defaults = [
        ("pending", "招领中", 1),
        ("matched", "匹配中", 2),
        ("claimed", "已认领", 3),
        ("expired", "已过期", 4),
        ("offline", "已下架", 5),
    ]
    for code, label, sort_order in defaults:
        row = (
            db.query(DictionaryItem)
            .filter(DictionaryItem.dict_type == "item_status", DictionaryItem.code == code)
            .first()
        )
        if row:
            if not row.label:
                row.label = label
            if row.sort_order is None:
                row.sort_order = sort_order
            continue
        db.add(
            DictionaryItem(
                dict_type="item_status",
                code=code,
                label=label,
                sort_order=sort_order,
                status=1,
            )
        )


def _ensure_dictionary_submenus(db: Session) -> None:
    """将「数据字典管理」组织为父菜单，子菜单包含物品状态和物品分类。"""
    admin_r = db.query(Role).filter(Role.code == "admin").first()
    super_r = db.query(Role).filter(Role.code == "super_admin").first()

    parent = db.query(Menu).filter(Menu.path == "/admin/dictionary").first()
    if not parent:
        parent = Menu(
            parent_id=0,
            name="数据字典管理",
            path="/admin/dictionary",
            icon="Collection",
            permission="sys:dict:manage",
            sort=7,
            visible=1,
        )
        db.add(parent)
        db.flush()
    else:
        parent.name = "数据字典管理"
        parent.icon = "Collection"
        parent.permission = "sys:dict:manage"

    old_category_menu = db.query(Menu).filter(Menu.path == "/admin/item-categories").first()
    if old_category_menu:
        old_category_menu.path = "/admin/dictionary/category"
        old_category_menu.name = "物品分类"
        old_category_menu.parent_id = parent.id
        old_category_menu.permission = "sys:dict:item-category"

    children = [
        ("/admin/dictionary/status", "物品状态", "Tickets", "sys:dict:item-status", 1),
        ("/admin/dictionary/category", "物品分类", "CollectionTag", "sys:dict:item-category", 2),
    ]
    for path, name, icon, perm, sort in children:
        m = db.query(Menu).filter(Menu.path == path).first()
        if not m:
            m = Menu(
                parent_id=parent.id,
                name=name,
                path=path,
                icon=icon,
                permission=perm,
                sort=sort,
                visible=1,
            )
            db.add(m)
            db.flush()
        else:
            m.parent_id = parent.id
            m.name = name
            m.icon = icon
            m.permission = perm
            m.sort = sort
        if admin_r:
            _ensure_role_menu(db, admin_r.id, m.id)
        if super_r:
            _ensure_role_menu(db, super_r.id, m.id)
