import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from celery import chain

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..tasks.ocr_tasks import extract_text_from_image_task
from ..tasks.ledger_tasks import analyze_ledger_text, wrap_analyze_text_with_entry_id, merge_text_and_analyze, update_ledger_entry
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
    
    # 验证输入
    if not raw_text and not image_path:
        raise HTTPException(status_code=400, detail="必须提供 text 或 image")
    
    # 保存原始的 raw_text（如果存在，用于后续合并）
    original_text = raw_text if raw_text else None
    
    # 创建账本条目（初始状态为 pending）
    entry = models.LedgerEntry(
        user_id=current_user.id,
        raw_text=raw_text or "",  # 如果没有文本，先设为空字符串
        status="pending",
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    
    # 构建任务链
    if image_path:
        # 有图片：OCR -> 合并文本并分析 -> 更新数据库
        original_text_for_merge = original_text  # 保存用于后续合并
        
        # 创建任务链：OCR -> 合并文本并分析 -> 更新数据库
        # merge_text_and_analyze 接收 OCR 结果作为第一个参数，original_text 和 entry_id 作为额外参数
        task_chain = chain(
            extract_text_from_image_task.s(image_path),
            merge_text_and_analyze.s(original_text_for_merge, entry.id),
            update_ledger_entry.s()
        )
    else:
        # 只有文本：直接 LLM -> 更新数据库
        # 使用包装任务添加 entry_id
        task_chain = chain(
            wrap_analyze_text_with_entry_id.s(raw_text, entry.id),
            update_ledger_entry.s()
        )
    
    # 启动任务链（异步执行，不等待）
    result = task_chain.apply_async()
    
    # 保存任务 ID
    entry.task_id = result.id
    entry.status = "processing"
    await session.commit()
    await session.refresh(entry)
    
    return entry


@router.get("/{ledger_id}", response_model=schemas.LedgerOut)
async def get_ledger(
    ledger_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """获取单个账本条目（用于轮询状态）"""
    result = await session.execute(
        select(models.LedgerEntry)
        .where(models.LedgerEntry.id == ledger_id)
        .where(models.LedgerEntry.user_id == current_user.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="账本条目不存在")
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

