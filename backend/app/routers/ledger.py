import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..tasks.ocr_tasks import extract_text_from_image_task
from ..tasks.ledger_tasks import analyze_ledger_text
from ..utils.file_utils import save_uploaded_img

router = APIRouter(prefix="/ledger", tags=["ledger"])

# 图片上传目录（复用 notes 的目录）
UPLOAD_DIR = Path("uploads")
IMAGE_DIR = UPLOAD_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

#用于获取当前用户的所有记账条目
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

#用于创建新的记账条目
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
    
    处理流程：
    1. 如果有图片，先通过消息队列进行 OCR 提取文本
    2. OCR 完成后，通过消息队列进行 LLM 分析
    3. 保存账本条目
    """
    raw_text = ""
    image_path = None

    #从请求头里取出 "content-type" 字段
    # 如果这个字段不存在，则默认返回 ""（空字符串）
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
                # 使用通用函数保存图片文件
                image_path = await save_uploaded_img(image_file, IMAGE_DIR)
        # 检查是否有文本字段
        elif "text" in form:
            raw_text = form["text"]
        
        if not raw_text and not image_path:
            raise HTTPException(status_code=400, detail="必须提供 text 或 image")
    else:
        raise HTTPException(status_code=400, detail="不支持的 Content-Type，请使用 application/json 或 multipart/form-data")
    
    # 如果有图片路径，先通过消息队列进行 OCR
    if image_path:
        # 调用 OCR 任务（通过 Celery 消息队列）
        ocr_task = extract_text_from_image_task.delay(image_path)
        # 等待 OCR 完成
        ocr_text = await asyncio.to_thread(ocr_task.get, timeout=300)  # 5 分钟超时
        
        if not ocr_text or not ocr_text.strip():
            raise HTTPException(status_code=400, detail="OCR 未能从图片中提取文本")
        
        raw_text = ocr_text
    
    # 如果 raw_text 为空，说明无法提取文本
    if not raw_text:
        raise HTTPException(status_code=400, detail="无法从输入中提取文本")
    
    # 调用 LLM 分析任务
    llm_task = analyze_ledger_text.delay(raw_text)
    # 等待 LLM 分析完成
    ai_result = await asyncio.to_thread(llm_task.get, timeout=300)  # 5 分钟超时
    
    # 创建账本条目
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

