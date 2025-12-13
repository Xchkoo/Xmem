from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from typing import Optional
import json
import logging
import datetime as dt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from celery import chain

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..tasks.ocr_tasks import extract_text_from_image_task
from ..tasks.ledger_tasks import analyze_ledger_text, wrap_analyze_text_with_entry_id, merge_text_and_analyze, update_ledger_entry
from ..utils.file_utils import save_uploaded_img
from ..constants import LEDGER_CATEGORIES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ledger", tags=["ledger"])

# 图片上传目录（复用 notes 的目录）
UPLOAD_DIR = Path("uploads")
IMAGE_DIR = UPLOAD_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

#用于获取当前用户的所有记账条目
@router.get("", response_model=list[schemas.LedgerOut])
async def list_ledgers(
    category: Optional[str] = None,
    session: AsyncSession = Depends(get_session), 
    current_user: models.User = Depends(get_current_user)
):
    """
    获取当前用户的所有记账条目
    
    Args:
        category: 可选的分类筛选参数，必须是 LEDGER_CATEGORIES 中的值
    """
    query = select(models.LedgerEntry).where(models.LedgerEntry.user_id == current_user.id)
    
    # 如果提供了分类筛选，验证并添加筛选条件
    if category is not None:
        if category not in LEDGER_CATEGORIES:
            raise HTTPException(
                status_code=400, 
                detail=f"分类必须是以下之一: {', '.join(LEDGER_CATEGORIES)}"
            )
        query = query.where(models.LedgerEntry.category == category)
    
    query = query.order_by(models.LedgerEntry.created_at.desc())
    
    result = await session.execute(query)
    return result.scalars().all()

#用于创建新的记账条目
@router.post("", response_model=schemas.LedgerOut)
async def create_ledger(
    request: Request,
    background_tasks: BackgroundTasks,
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

    # 从请求头里取出 "content-type" 字段，转换为小写以便比较
    content_type = request.headers.get("content-type", "").lower()
    
    # 处理 JSON 请求（前端发送的格式）
    if content_type.startswith("application/json"):
        try:
            body = await request.json()
            raw_text = body.get("text", "")
            if not raw_text:
                raise HTTPException(status_code=400, detail="必须提供 text 字段")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="无效的 JSON 格式")

    # 处理 multipart/form-data 请求（用于图片上传）
    elif content_type.startswith("multipart/form-data"):
        try:
            form = await request.form()
            
            # 检查是否有图片上传
            if "image" in form:
                image_file = form["image"]
                if hasattr(image_file, "file"):  # UploadFile 对象
                    # 使用通用函数保存图片文件
                    image_path = await save_uploaded_img(image_file, IMAGE_DIR)
                    logger.info(f"图片已保存: {image_path}")
            # 检查是否有文本字段
            if "text" in form:
                raw_text = form["text"]
            
            if not raw_text and not image_path:
                raise HTTPException(status_code=400, detail="必须提供 text 或 image")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"处理 multipart/form-data 失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"处理表单数据失败: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="不支持的 Content-Type，请使用 application/json 或 multipart/form-data")
    
    # 验证输入
    if not raw_text and not image_path:
        raise HTTPException(status_code=400, detail="必须提供 text 或 image")
    
    # 保存原始的 raw_text（如果存在，用于后续合并）
    original_text = raw_text if raw_text else None
    
    # 创建账本条目（初始状态为 pending）
    logger.info(f"创建账本条目，user_id: {current_user.id}, has_text: {bool(raw_text)}, has_image: {bool(image_path)}")
    entry = models.LedgerEntry(
        user_id=current_user.id,
        raw_text=raw_text or "",  # 如果没有文本，先设为空字符串
        status="pending",
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    logger.info(f"账本条目已创建，entry_id: {entry.id}, status: {entry.status}")
    
    # 立即返回 pending 状态的 entry，让前端可以立即显示
    entry_id = entry.id
    
    # 保存变量到局部作用域，避免闭包问题
    task_image_path = image_path
    task_raw_text = raw_text
    task_original_text = original_text
    
    def start_celery_task():
        """后台任务：启动 Celery 任务链并更新状态"""
        try:
            logger.info(f"[后台任务] 开始启动 Celery 任务链，entry_id: {entry_id}, has_image: {bool(task_image_path)}")
            
            # 构建任务链
            if task_image_path:
                # 有图片：OCR -> 合并文本并分析 -> 更新数据库
                logger.info(f"[后台任务] 构建 OCR 任务链，image_path: {task_image_path}")
                task_chain = chain(
                    extract_text_from_image_task.s(task_image_path),
                    merge_text_and_analyze.s(task_original_text, entry_id),
                    update_ledger_entry.s()
                )
            else:
                # 只有文本：直接 LLM -> 更新数据库
                logger.info(f"[后台任务] 构建文本分析任务链，text: {task_raw_text[:50] if task_raw_text else 'None'}...")
                task_chain = chain(
                    wrap_analyze_text_with_entry_id.s(task_raw_text, entry_id),
                    update_ledger_entry.s()
                )
            
            # 启动任务链（在后台线程中执行，不会阻塞主请求）
            celery_result = task_chain.apply_async()
            logger.info(f"[后台任务] Celery 任务链已启动，task_id: {celery_result.id}, entry_id: {entry_id}")
            
            # 在后台线程中更新数据库状态（使用同步数据库连接）
            from ..tasks.ledger_tasks import SyncSessionLocal
            from sqlalchemy.orm import Session
            sync_session: Session = SyncSessionLocal()
            try:
                entry_to_update = sync_session.query(models.LedgerEntry).filter(models.LedgerEntry.id == entry_id).first()
                if entry_to_update:
                    entry_to_update.task_id = celery_result.id
                    entry_to_update.status = "processing"
                    sync_session.commit()
                    logger.info(f"[后台任务] 已更新 entry {entry_id} 状态为 processing，task_id: {celery_result.id}")
                else:
                    logger.error(f"[后台任务] 无法找到 entry_id: {entry_id}")
            finally:
                sync_session.close()
                
        except Exception as e:
            logger.error(f"[后台任务] 启动 Celery 任务链失败，entry_id: {entry_id}, 错误: {str(e)}", exc_info=True)
            # 尝试更新状态为失败
            try:
                from ..tasks.ledger_tasks import SyncSessionLocal
                sync_session = SyncSessionLocal()
                try:
                    entry_error = sync_session.query(models.LedgerEntry).filter(models.LedgerEntry.id == entry_id).first()
                    if entry_error:
                        entry_error.status = "failed"
                        sync_session.commit()
                        logger.info(f"[后台任务] 已将 entry {entry_id} 状态更新为 failed")
                finally:
                    sync_session.close()
            except Exception as update_error:
                logger.error(f"[后台任务] 更新失败状态时出错: {str(update_error)}", exc_info=True)
    
    # 使用 FastAPI 的 BackgroundTasks 添加后台任务
    # BackgroundTasks 会在响应返回后执行，不会阻塞主请求
    background_tasks.add_task(start_celery_task)
    logger.info(f"已添加后台任务，entry_id: {entry_id}，将在响应返回后执行")
    
    return entry


@router.get("/summary")
async def summary(
    session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)
):
    """获取账本摘要（必须在 /{ledger_id} 之前定义，避免路由冲突）"""
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


@router.patch("/{ledger_id}", response_model=schemas.LedgerOut)
async def update_ledger(
    ledger_id: int,
    payload: schemas.LedgerUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """更新账本条目"""
    result = await session.execute(
        select(models.LedgerEntry)
        .where(models.LedgerEntry.id == ledger_id)
        .where(models.LedgerEntry.user_id == current_user.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="账本条目不存在")
    
    # 更新字段
    if payload.amount is not None:
        entry.amount = payload.amount
    if payload.currency is not None:
        entry.currency = payload.currency
    if payload.category is not None:
        # 验证分类是否在允许的列表中（双重验证，确保安全）
        if payload.category not in LEDGER_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"分类必须是以下之一: {', '.join(LEDGER_CATEGORIES)}"
            )
        entry.category = payload.category
    if payload.merchant is not None:
        entry.merchant = payload.merchant
    if payload.raw_text is not None:
        entry.raw_text = payload.raw_text
    if payload.event_time is not None:
        # 将带时区的 datetime 转换为不带时区的 datetime（naive datetime）
        # 因为数据库字段是 TIMESTAMP WITHOUT TIME ZONE
        if payload.event_time.tzinfo is not None:
            # 如果有时区信息，转换为 UTC 然后移除时区信息
            entry.event_time = payload.event_time.astimezone(dt.timezone.utc).replace(tzinfo=None)
        else:
            # 如果没有时区信息，直接使用
            entry.event_time = payload.event_time
    
    await session.commit()
    await session.refresh(entry)
    return entry


@router.delete("/{ledger_id}")
async def delete_ledger(
    ledger_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """删除账本条目"""
    result = await session.execute(
        select(models.LedgerEntry)
        .where(models.LedgerEntry.id == ledger_id)
        .where(models.LedgerEntry.user_id == current_user.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="账本条目不存在")
    
    await session.delete(entry)
    await session.commit()
    return {"message": "账本条目已删除"}

