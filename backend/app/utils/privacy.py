from __future__ import annotations

import re


def redact_description(text: str | None, *, max_len: int = 100) -> str | None:
    """对公开展示的描述做脱敏：长数字、手机、邮箱等打码，并截断长度。"""
    if not text:
        return text
    t = text.strip()
    t = re.sub(r"\d{5,}", lambda m: "*" * min(12, len(m.group())), t)
    t = re.sub(r"1[3-9]\d{9}", "***********", t)
    t = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "***@***", t)
    if len(t) > max_len:
        t = t[:max_len].rstrip() + "…"
    return t


def mask_location_public(loc: str | None) -> str | None:
    """只展示地点中第一段/粗略区域，减少凭地点冒领。"""
    if not loc or not loc.strip():
        return loc
    s = loc.strip()
    parts = re.split(r"[，,、；;·\|／/]", s)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return "地点已隐藏"
    head = parts[0]
    if len(parts) > 1 or len(s) > len(head) + 1:
        return f"{head}（后续详细位置已隐藏）"
    if len(head) > 16:
        return head[:16].rstrip() + "…"
    return head


def mask_middle_30(text: str | None) -> str | None:
    """账号脱敏：中间约 30% 以 * 替换，保留首尾可识别性。"""
    if text is None:
        return None
    s = text.strip()
    n = len(s)
    if n <= 1:
        return s
    mask_len = max(1, round(n * 0.3))
    if mask_len >= n:
        mask_len = n - 1
    start = max(1, (n - mask_len) // 2)
    end = start + mask_len
    return s[:start] + ("*" * mask_len) + s[end:]
