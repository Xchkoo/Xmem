import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..services import ledger_ai, ocr

router = APIRouter(prefix="/ledger", tags=["ledger"])

# 图片上传目录（复用 notes 的目录）
UPLOAD_DIR = Path("uploads")
IMAGE_DIR = UPLOAD_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=list[schemas.LedgerOut])
async def list_ledgers(
    session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)
):
    result = await session.execute(
        select(models.LedgerEntry)
        .where(models.LedgerEntry.user_id == current_user.id)
        .order_by(models.LedgerEntry.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=schemas.LedgerOut)
async def create_ledger(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """
    创建账本条目
    支持两种方式：
    1. JSON 格式：{"text": "..."} - 用于前端文本输入
    2. multipart/form-data：text=... 或 image=... - 用于表单提交和图片上传
    """
    raw_text = ""
    content_type = request.headers.get("content-type", "")
    
    # 处理 JSON 请求（前端发送的格式）
    if "application/json" in content_type:
        try:
            body = await request.json()
            raw_text = body.get("text", "")
            if not raw_text:
                raise HTTPException(status_code=400, detail="必须提供 text 字段")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="无效的 JSON 格式")
    # 处理 multipart/form-data 请求（用于图片上传）
    elif "multipart/form-data" in content_type:
        form = await request.form()
        
        # 检查是否有图片上传
        if "image" in form:
            image_file = form["image"]
            if hasattr(image_file, "file"):  # UploadFile 对象
                # 保存图片文件
                file_ext = Path(image_file.filename).suffix if image_file.filename else ".jpg"
                file_name = f"{uuid.uuid4()}{file_ext}"
                file_path = IMAGE_DIR / file_name
                
                content = await image_file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # 调用 OCR 提取文本
                ocr_text = await ocr.extract_text_from_image(str(file_path))
                raw_text = ocr_text
        # 检查是否有文本字段
        elif "text" in form:
            raw_text = form["text"]
        
        if not raw_text:
            raise HTTPException(status_code=400, detail="必须提供 text 或 image")
    else:
        raise HTTPException(status_code=400, detail="不支持的 Content-Type，请使用 application/json 或 multipart/form-data")
    
    if not raw_text:
        raise HTTPException(status_code=400, detail="无法从输入中提取文本")
    
    # 使用 Celery 任务队列进行 AI 分析
    # ledger_ai.analyze 默认使用 Celery 异步任务队列处理
    ai_result = await ledger_ai.analyze(raw_text)
    
    entry = models.LedgerEntry(
        user_id=current_user.id,
        raw_text=raw_text,
        amount=ai_result.get("amount"),
        currency=ai_result.get("currency", "CNY"),
        category=ai_result.get("category"),
        merchant=ai_result.get("merchant"),
        event_time=ai_result.get("event_time"),
        meta=ai_result.get("meta"),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.get("/summary")
async def summary(
    session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)
):
    total_amount = await session.execute(
        select(func.coalesce(func.sum(models.LedgerEntry.amount), 0)).where(
            models.LedgerEntry.user_id == current_user.id
        )
    )
    total = total_amount.scalar() or 0
    recent = await session.execute(
        select(models.LedgerEntry)
        .where(models.LedgerEntry.user_id == current_user.id)
        .order_by(models.LedgerEntry.created_at.desc())
        .limit(5)
    )
    return {"total_amount": total, "recent": recent.scalars().all()}

