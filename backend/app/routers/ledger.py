from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query
from typing import Optional
import json
import logging
import datetime as dt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from celery import chain

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..tasks.ocr_tasks import extract_text_from_image_task
from ..tasks.ledger_tasks import analyze_ledger_text, wrap_analyze_text_with_entry_id, merge_text_and_analyze, update_ledger_entry
from ..utils.file_utils import save_uploaded_img

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ledger", tags=["ledger"])

# 图片上传目录（复用 notes 的目录）
UPLOAD_DIR = Path("uploads")
IMAGE_DIR = UPLOAD_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

#用于获取当前用户的所有记账条目（支持分页）
@router.get("", response_model=schemas.LedgerListResponse)
async def list_ledgers(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    session: AsyncSession = Depends(get_session), 
    current_user: models.User = Depends(get_current_user)
):
    """
    获取当前用户的所有记账条目（支持分页）
    
    Args:
        page: 页码，从1开始
        page_size: 每页数量，最大100
        category: 可选的分类筛选参数
    """
    try:
        from ..constants import LEDGER_CATEGORIES
        
        logger.info(f"获取记账列表，user_id: {current_user.id}, page: {page}, page_size: {page_size}, category: {category}")
        
        # 构建查询
        query = select(models.LedgerEntry).where(models.LedgerEntry.user_id == current_user.id)
        
        # 如果提供了分类筛选，验证并添加筛选条件
        if category is not None:
            if category not in LEDGER_CATEGORIES:
                raise HTTPException(
                    status_code=400, 
                    detail=f"分类必须是以下之一: {', '.join(LEDGER_CATEGORIES)}"
                )
            query = query.where(models.LedgerEntry.category == category)
        
        # 计算总数（使用原始查询，不包含 order_by, offset, limit）
        count_query = select(func.count(models.LedgerEntry.id)).where(models.LedgerEntry.user_id == current_user.id)
        if category is not None:
            count_query = count_query.where(models.LedgerEntry.category == category)
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0
        logger.info(f"查询到总数: {total}")
        
        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(models.LedgerEntry.created_at.desc()).offset(offset).limit(page_size)
        
        result = await session.execute(query)
        items = result.scalars().all()
        logger.info(f"查询到 {len(items)} 条记录")
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return schemas.LedgerListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取记账列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取记账列表失败: {str(e)}")

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


@router.get("/statistics", response_model=schemas.LedgerStatisticsResponse)
async def get_ledger_statistics(
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """获取记账统计数据（必须在 /{ledger_id} 之前定义，避免路由冲突）"""
    from ..constants import LEDGER_CATEGORIES
    
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    
    # 获取所有已完成的记账条目
    query = select(models.LedgerEntry).where(
        models.LedgerEntry.user_id == current_user.id,
        models.LedgerEntry.status == "completed",
        models.LedgerEntry.amount.isnot(None)
    )
    result = await session.execute(query)
    entries = result.scalars().all()
    
    # 计算近6个月数据
    monthly_data: list[schemas.MonthlyStats] = []
    for i in range(5, -1, -1):  # 从5个月前到当前月
        # 计算月份
        target_month = now.month - i
        target_year = now.year
        while target_month < 1:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        month_str = f"{target_year}-{target_month:02d}"
        
        month_amount = 0.0
        month_count = 0
        
        for entry in entries:
            entry_date = entry.event_time or entry.created_at
            if entry_date.year == target_year and entry_date.month == target_month:
                month_amount += entry.amount or 0
                month_count += 1
        
        monthly_data.append(schemas.MonthlyStats(
            month=month_str,
            amount=month_amount,
            count=month_count
        ))
    
    # 计算全年数据
    yearly_data: list[schemas.MonthlyStats] = []
    current_year = now.year
    for month in range(1, 13):
        month_str = f"{current_year}-{month:02d}"
        month_amount = 0.0
        month_count = 0
        
        for entry in entries:
            entry_date = entry.event_time or entry.created_at
            if entry_date.year == current_year and entry_date.month == month:
                month_amount += entry.amount or 0
                month_count += 1
        
        yearly_data.append(schemas.MonthlyStats(
            month=month_str,
            amount=month_amount,
            count=month_count
        ))
    
    # 计算分类统计
    category_stats_dict: dict[str, dict] = {}
    total_amount = 0.0
    
    for entry in entries:
        if not entry.category or not entry.amount:
            continue
        
        if entry.category not in category_stats_dict:
            category_stats_dict[entry.category] = {"amount": 0.0, "count": 0}
        
        category_stats_dict[entry.category]["amount"] += entry.amount
        category_stats_dict[entry.category]["count"] += 1
        total_amount += entry.amount
    
    category_stats: list[schemas.CategoryStats] = []
    for category, data in category_stats_dict.items():
        percentage = (data["amount"] / total_amount * 100) if total_amount > 0 else 0
        category_stats.append(schemas.CategoryStats(
            category=category,
            amount=data["amount"],
            count=data["count"],
            percentage=percentage
        ))
    
    # 按金额排序
    category_stats.sort(key=lambda x: x.amount, reverse=True)
    
    # 计算月度对比
    current_month_total = monthly_data[-1].amount if monthly_data else 0.0
    last_month_total = monthly_data[-2].amount if len(monthly_data) > 1 else 0.0
    month_diff = current_month_total - last_month_total
    month_diff_percent = (month_diff / last_month_total * 100) if last_month_total > 0 else 0.0
    
    return schemas.LedgerStatisticsResponse(
        monthly_data=monthly_data,
        yearly_data=yearly_data,
        category_stats=category_stats,
        current_month_total=current_month_total,
        last_month_total=last_month_total,
        month_diff=month_diff,
        month_diff_percent=month_diff_percent
    )


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

