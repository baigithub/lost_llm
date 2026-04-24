from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.setting import SystemSetting

HOME_LIST_PAGE_SIZE_KEY = "home_list_page_size"
DEFAULT_HOME_LIST_PAGE_SIZE = 20
MIN_HOME_LIST_PAGE_SIZE = 5
MAX_HOME_LIST_PAGE_SIZE = 100


def get_home_list_page_size(db: Session) -> int:
    row = db.query(SystemSetting).filter(SystemSetting.key == HOME_LIST_PAGE_SIZE_KEY).first()
    if not row or not row.value:
        return DEFAULT_HOME_LIST_PAGE_SIZE
    try:
        n = int(row.value)
        return max(MIN_HOME_LIST_PAGE_SIZE, min(MAX_HOME_LIST_PAGE_SIZE, n))
    except ValueError:
        return DEFAULT_HOME_LIST_PAGE_SIZE


def set_home_list_page_size(db: Session, page_size: int) -> int:
    n = max(MIN_HOME_LIST_PAGE_SIZE, min(MAX_HOME_LIST_PAGE_SIZE, int(page_size)))
    row = db.query(SystemSetting).filter(SystemSetting.key == HOME_LIST_PAGE_SIZE_KEY).first()
    if row:
        row.value = str(n)
    else:
        db.add(SystemSetting(key=HOME_LIST_PAGE_SIZE_KEY, value=str(n)))
    db.commit()
    return n


def ensure_default_system_settings(db: Session) -> None:
    if not db.query(SystemSetting).filter(SystemSetting.key == HOME_LIST_PAGE_SIZE_KEY).first():
        db.add(SystemSetting(key=HOME_LIST_PAGE_SIZE_KEY, value=str(DEFAULT_HOME_LIST_PAGE_SIZE)))
