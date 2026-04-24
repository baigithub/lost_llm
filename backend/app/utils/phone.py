from __future__ import annotations
def mask_phone(phone: str | None) -> str | None:
    if not phone or len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def mask_phone_optional(phone: str | None) -> str | None:
    return mask_phone(phone)
