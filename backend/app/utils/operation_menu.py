"""根据操作日志中的请求路径解析对应后台菜单中文名（与 menus.path 最长前缀匹配）。"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.menu import Menu


def _normalize_admin_path(path: str | None) -> str:
    if not path:
        return ""
    p = path.strip()
    if not p:
        return ""
    if p.startswith("/api/v1/"):
        p = p[len("/api/v1") :]
    elif p.startswith("/api/v1"):
        p = p[len("/api/v1") :]
    if not p.startswith("/"):
        p = "/" + p
    if p.endswith("/") and p != "/":
        p = p.rstrip("/")
    return p


def _candidate_menu_paths(api_path: str) -> list[str]:
    """将后台 API 路径映射为可能的后台菜单路由。"""
    out = [api_path]
    aliases = (
        ("/admin/logs/login", "/admin/logs"),
        ("/admin/logs/operation", "/admin/logs"),
        ("/admin/logs/exception", "/admin/logs"),
        ("/admin/claims/", "/admin/claims"),
        ("/admin/categories", "/admin/dictionary/category"),
        ("/admin/dictionary/item-status", "/admin/dictionary/status"),
    )
    for src, dst in aliases:
        if api_path == src or api_path.startswith(src + "/"):
            out.append(dst)
    # 兜底：字典接口都归到数据字典菜单
    if api_path == "/admin/dictionary" or api_path.startswith("/admin/dictionary/"):
        out.extend(("/admin/dictionary/status", "/admin/dictionary/category", "/admin/dictionary"))
    return out


def make_menu_name_resolver(db: Session) -> Callable[[str | None], str]:
    """构建解析函数；同一请求内应复用，避免每条日志重复查库。"""
    rows = (
        db.query(Menu)
        .filter(Menu.path.isnot(None), Menu.path != "")
        .order_by(func.length(Menu.path).desc())
        .all()
    )
    pairs: list[tuple[str, str]] = []
    for m in rows:
        p = _normalize_admin_path(m.path)
        if not p.startswith("/admin"):
            continue
        pairs.append((p, m.name or ""))

    def resolve(api_path: str | None) -> str:
        if not api_path:
            return ""
        normalized = _normalize_admin_path(api_path)
        if not normalized.startswith("/admin"):
            return ""
        for candidate in _candidate_menu_paths(normalized):
            for p, name in pairs:
                if candidate == p or candidate.startswith(p + "/"):
                    return name
        return ""

    return resolve
