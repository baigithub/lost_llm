from __future__ import annotations
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import settings
from app.deps import get_current_user
from app.models.user import User
from app.schemas.common import ok
from app.services.recognition import recognition_service

router = APIRouter()


@router.post("/upload")
async def recognize_upload(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="仅支持图片文件")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png"):
        raise HTTPException(400, detail="仅支持 jpg/png")
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, detail=f"文件不能超过 {settings.MAX_UPLOAD_MB}MB")
    date_path = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(settings.UPLOAD_DIR, date_path)
    os.makedirs(save_dir, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(save_dir, name)
    with open(path, "wb") as f:
        f.write(content)
    rel = f"/uploads/{date_path}/{name}"
    image_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}{rel}"
    result = await recognition_service.recognize(path)
    return ok({"image_url": image_url, "recognition": result})
