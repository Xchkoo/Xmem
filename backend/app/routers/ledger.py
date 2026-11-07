from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query
from fastapi.responses import FileResponse
from typing import Optional
import json
import logging
import datetime as dt
import calendar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.exc import SQLAlchemyError
from celery import chain

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..tasks.ocr_tasks import extract_text_from_image_task
from ..tasks.ledger_tasks import (
    wrap_analyze_text_with_entry_id,
    merge_text_and_analyze,
    update_ledger_entry,
)
from ..services import ai as ai_service
from ..utils.file_utils import save_uploaded_img, make_thumbnail
from ..utils.exchange_rate import get_exchange_rate_to_cny, convert_to_cny
from ..constants import LEDGER_CATEGORIES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ledger", tags=["ledger"])

# 图片上传目录（复用 notes 的目录）
UPLOAD_DIR = Path("uploads")
IMAGE_DIR = UPLOAD_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _parse_month(value: str) -> dt.datetime:
    """解析 YYYY-MM 字符串并返回该月第一天。"""
    try:
        return dt.datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="月份格式必须为 YYYY-MM") from exc


def _format_month(year: int, month: int) -> str:
    """格式化月份为 YYYY-MM 字符串。"""
    return f"{year}-{month:02d}"


def _add_months(year: int, month: int, offset: int) -> tuple[int, int]:
    """基于偏移量计算新的年月。"""
    total = (year * 12 + (month - 1)) + offset
    new_year = total // 12
    new_month = total % 12 + 1
    return new_year, new_month


def _normalize_currency(value: str) -> str:
    """标准化并校验货币代码。"""
    currency = value.strip().upper().split()[0] if isinstance(value, str) else ""
    if currency not in {"CNY", "USD", "EUR", "JPY"}:
        raise HTTPException(status_code=400, detail="货币必须是 CNY、USD、EUR、JPY 之一")
    return currency


async def _get_or_inherit_budget(
    session: AsyncSession,
    user_id: int,
    month: str,
) -> models.LedgerBudget | None:
    """获取预算，如不存在则继承上个月的预算。"""
    result = await session.execute(
        select(models.LedgerBudget).where(
            models.LedgerBudget.user_id == user_id,
            models.LedgerBudget.month == month,
        )
    )
    budget = result.scalar_one_or_none()
    if budget:
        return budget
    parsed = _parse_month(month)
    prev_year, prev_month = _add_months(parsed.year, parsed.month, -1)
    prev_month_str = _format_month(prev_year, prev_month)
    prev_result = await session.execute(
        select(models.LedgerBudget).where(
            models.LedgerBudget.user_id == user_id,
            models.LedgerBudget.month == prev_month_str,
        )
    )
    prev_budget = prev_result.scalar_one_or_none()
    if not prev_budget:
        return None
    budget = models.LedgerBudget(
        user_id=user_id,
        month=month,
        amount=prev_budget.amount,
        currency=prev_budget.currency or "CNY",
    )
    session.add(budget)
    await session.commit()
    await session.refresh(budget)
    return budget


async def _build_budget_out(
    budget: models.LedgerBudget,
    exchange_rates: dict[str, float],
) -> schemas.LedgerBudgetOut:
    """构建带折算金额的预算响应。"""
    currency = budget.currency or "CNY"
    rate = exchange_rates.get(currency)
    if rate is None:
        rate = await get_exchange_rate_to_cny(currency)
        exchange_rates[currency] = rate
    amount_cny = convert_to_cny(budget.amount, currency, rate)
    return schemas.LedgerBudgetOut(
        month=budget.month,
        amount=budget.amount,
        currency=currency,
        amount_cny=amount_cny,
    )


def _resolve_target_year(month_value: str, year_value: int | None) -> int:
    """解析统计使用的目标年份。"""
    if year_value is not None:
        if year_value < 1970 or year_value > 2100:
            raise HTTPException(status_code=400, detail="年份范围必须在 1970-2100")
        return year_value
    parsed = _parse_month(month_value)
    return parsed.year


def _build_ledger_summary_text(entries: list[models.LedgerEntry]) -> str:
    """构建用于 AI 总结的记账文本。"""
    lines: list[str] = []
    for entry in entries:
        entry_date = entry.event_time or entry.created_at
        date_label = entry_date.strftime("%Y-%m-%d")
        amount = entry.amount or 0
        currency = entry.currency or "CNY"
        category = entry.category or "未分类"
        merchant = entry.merchant or "未知商家"
        lines.append(f"{date_label} | {amount} {currency} | {category} | {merchant}")
    return "\n".join(lines)


def _get_ledger_note_for_month(user_id: int, month: str):
    """查询指定月份的记账笔记。"""
    return (
        select(models.Note)
        .where(
            models.Note.user_id == user_id,
            models.Note.is_ledger_note.is_(True),
            models.Note.ledger_month == month,
        )
        .order_by(models.Note.created_at.desc())
        .limit(1)
    )

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
    image_thumb_path = ""

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
                    # 列表页用的缩略图；生成失败不影响主流程
                    image_thumb_path = make_thumbnail(image_path)
                    if image_thumb_path:
                        logger.info(f"缩略图已生成: {image_thumb_path}")
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
        # 原图与缩略图作为「证据」长期保留，OCR 文本只用于 AI 分析
        image_path=image_path,
        image_thumb_path=image_thumb_path or None,
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


@router.get("/budget", response_model=Optional[schemas.LedgerBudgetOut])
async def get_ledger_budget(
    month: Optional[str] = Query(None, description="预算月份，格式 YYYY-MM"),
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """获取当前用户指定月份的预算。"""
    target_month = month or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
    _parse_month(target_month)
    budget = await _get_or_inherit_budget(session, current_user.id, target_month)
    if not budget:
        return None
    exchange_rates: dict[str, float] = {}
    return await _build_budget_out(budget, exchange_rates)


@router.put("/budget", response_model=schemas.LedgerBudgetOut)
async def upsert_ledger_budget(
    payload: schemas.LedgerBudgetIn,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """创建或更新指定月份的预算。"""
    target_month = payload.month
    _parse_month(target_month)
    if payload.amount < 0:
        raise HTTPException(status_code=400, detail="预算金额不能为负数")
    currency = _normalize_currency(payload.currency)
    result = await session.execute(
        select(models.LedgerBudget).where(
            models.LedgerBudget.user_id == current_user.id,
            models.LedgerBudget.month == target_month,
        )
    )
    budget = result.scalar_one_or_none()
    if budget:
        budget.amount = payload.amount
        budget.currency = currency
        budget.updated_at = models.utc_now()
    else:
        budget = models.LedgerBudget(
            user_id=current_user.id,
            month=target_month,
            amount=payload.amount,
            currency=currency,
        )
        session.add(budget)
    await session.commit()
    await session.refresh(budget)
    exchange_rates: dict[str, float] = {}
    return await _build_budget_out(budget, exchange_rates)


@router.post("/statistics/ai-summary", response_model=schemas.LedgerMonthlySummaryOut)
async def generate_ledger_ai_summary(
    month: Optional[str] = Query(None, description="总结月份，格式 YYYY-MM"),
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """生成并保存记账月度 AI 总结。"""
    target_month = month or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
    parsed = _parse_month(target_month)

    query = select(models.LedgerEntry).where(
        models.LedgerEntry.user_id == current_user.id,
        models.LedgerEntry.status == "completed",
        models.LedgerEntry.amount.isnot(None),
    )
    result = await session.execute(query)
    entries = result.scalars().all()
    target_entries: list[models.LedgerEntry] = []
    for entry in entries:
        entry_date = entry.event_time or entry.created_at
        if entry_date.year == parsed.year and entry_date.month == parsed.month:
            target_entries.append(entry)

    if not target_entries:
        raise HTTPException(status_code=400, detail="该月份暂无可用记账数据")

    summary_text = _build_ledger_summary_text(target_entries)
    logger.info(
        "生成月度总结: user_id=%s, month=%s, entries=%s, text_length=%s",
        current_user.id,
        target_month,
        len(target_entries),
        len(summary_text),
    )
    try:
        summary = ai_service.generate_ledger_monthly_summary(summary_text)
        if not summary or not summary.strip():
            raise HTTPException(status_code=400, detail="AI 返回空总结内容")
    except ValueError as error:
        logger.exception("生成月度总结失败: user_id=%s, month=%s", current_user.id, target_month)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("生成月度总结失败: user_id=%s, month=%s", current_user.id, target_month)
        raise HTTPException(status_code=500, detail=f"AI 总结失败: {str(error)}") from error
    last_entry_at = max(entry.updated_at or entry.created_at for entry in target_entries)

    summary_record_result = await session.execute(
        select(models.LedgerMonthlySummary).where(
            models.LedgerMonthlySummary.user_id == current_user.id,
            models.LedgerMonthlySummary.month == target_month,
        )
    )
    summary_record = summary_record_result.scalar_one_or_none()
    if summary_record:
        summary_record.summary = summary
        summary_record.last_entry_at = last_entry_at
        summary_record.updated_at = models.utc_now()
    else:
        summary_record = models.LedgerMonthlySummary(
            user_id=current_user.id,
            month=target_month,
            summary=summary,
            last_entry_at=last_entry_at,
        )
        session.add(summary_record)

    note_result = await session.execute(_get_ledger_note_for_month(current_user.id, target_month))
    ledger_note = note_result.scalar_one_or_none()
    if ledger_note:
        ledger_note.ai_summary = summary

    await session.commit()
    return schemas.LedgerMonthlySummaryOut(summary=summary)


@router.get("/statistics", response_model=schemas.LedgerStatisticsResponse)
async def get_ledger_statistics(
    month: Optional[str] = Query(None, description="统计月份，格式 YYYY-MM"),
    year: Optional[int] = Query(None, description="统计年份，用于年度图表"),
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """获取记账统计数据（必须在 /{ledger_id} 之前定义，避免路由冲突）"""
    
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    target_month = month or now.strftime("%Y-%m")
    parsed_target_month = _parse_month(target_month)
    target_month_year = parsed_target_month.year
    target_month_value = parsed_target_month.month
    target_year = _resolve_target_year(target_month, year)
    
    # 获取所有已完成的记账条目
    query = select(models.LedgerEntry).where(
        models.LedgerEntry.user_id == current_user.id,
        models.LedgerEntry.status == "completed",
        models.LedgerEntry.amount.isnot(None)
    )
    result = await session.execute(query)
    entries = result.scalars().all()
    
    # 获取所有需要的汇率（批量获取，减少API调用）
    currencies_needed = set(entry.currency for entry in entries if entry.currency)
    exchange_rates: dict[str, float] = {}
    for currency in currencies_needed:
        try:
            exchange_rates[currency] = await get_exchange_rate_to_cny(currency)
        except Exception as e:
            logger.warning(f"获取 {currency} 汇率失败: {str(e)}，使用默认值")
            exchange_rates[currency] = await get_exchange_rate_to_cny(currency)  # 会使用默认值
    
    current_month_str = _format_month(target_month_year, target_month_value)

    # 计算近6个月数据
    monthly_data: list[schemas.MonthlyStats] = []
    for i in range(5, -1, -1):  # 从5个月前到当前月
        computed_year, computed_month = _add_months(target_month_year, target_month_value, -i)
        month_str = _format_month(computed_year, computed_month)
        
        month_amount = 0.0
        month_count = 0
        
        for entry in entries:
            entry_date = entry.event_time or entry.created_at
            if entry_date.year == computed_year and entry_date.month == computed_month:
                if entry.amount:
                    # 转换为人民币
                    currency = entry.currency or "CNY"
                    rate = exchange_rates.get(currency, 1.0)
                    month_amount += convert_to_cny(entry.amount, currency, rate)
                month_count += 1
        
        monthly_data.append(schemas.MonthlyStats(
            month=month_str,
            amount=month_amount,
            count=month_count
        ))
    
    # 计算全年数据
    yearly_data: list[schemas.MonthlyStats] = []
    current_year = target_year
    for month in range(1, 13):
        month_str = _format_month(current_year, month)
        month_amount = 0.0
        month_count = 0
        
        for entry in entries:
            entry_date = entry.event_time or entry.created_at
            if entry_date.year == current_year and entry_date.month == month:
                if entry.amount:
                    # 转换为人民币
                    currency = entry.currency or "CNY"
                    rate = exchange_rates.get(currency, 1.0)
                    month_amount += convert_to_cny(entry.amount, currency, rate)
                month_count += 1
        
        yearly_data.append(schemas.MonthlyStats(
            month=month_str,
            amount=month_amount,
            count=month_count
        ))

    # 计算近几年年度汇总
    yearly_totals: list[schemas.YearlyStats] = []
    for target_year_value in range(current_year - 4, current_year + 1):
        year_amount = 0.0
        year_count = 0
        for entry in entries:
            entry_date = entry.event_time or entry.created_at
            if entry_date.year == target_year_value:
                if entry.amount:
                    currency = entry.currency or "CNY"
                    rate = exchange_rates.get(currency, 1.0)
                    year_amount += convert_to_cny(entry.amount, currency, rate)
                year_count += 1
        yearly_totals.append(schemas.YearlyStats(
            year=target_year_value,
            amount=year_amount,
            count=year_count
        ))
    
    # 计算分类统计
    category_stats_dict: dict[str, dict] = {}
    total_amount = 0.0
    
    for entry in entries:
        if not entry.category or not entry.amount:
            continue
        
        # 转换为人民币
        currency = entry.currency or "CNY"
        rate = exchange_rates.get(currency, 1.0)
        amount_cny = convert_to_cny(entry.amount, currency, rate)
        
        if entry.category not in category_stats_dict:
            category_stats_dict[entry.category] = {"amount": 0.0, "count": 0}
        
        category_stats_dict[entry.category]["amount"] += amount_cny
        category_stats_dict[entry.category]["count"] += 1
        total_amount += amount_cny
    
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

    # 计算当前月日历数据
    days_in_month = calendar.monthrange(target_month_year, target_month_value)[1]
    daily_amounts: dict[int, float] = {day: 0.0 for day in range(1, days_in_month + 1)}
    daily_counts: dict[int, int] = {day: 0 for day in range(1, days_in_month + 1)}
    current_month_entries: list[models.LedgerEntry] = []
    for entry in entries:
        entry_date = entry.event_time or entry.created_at
        if entry_date.year == target_month_year and entry_date.month == target_month_value:
            current_month_entries.append(entry)
            day = entry_date.day
            currency = entry.currency or "CNY"
            rate = exchange_rates.get(currency, 1.0)
            if entry.amount:
                daily_amounts[day] += convert_to_cny(entry.amount, currency, rate)
            daily_counts[day] += 1

    daily_data: list[schemas.DailyStats] = []
    for day in range(1, days_in_month + 1):
        date_str = f"{target_month_year}-{target_month_value:02d}-{day:02d}"
        daily_data.append(
            schemas.DailyStats(
                date=date_str,
                amount=daily_amounts[day],
                count=daily_counts[day],
            )
        )

    # 获取预算
    budget = await _get_or_inherit_budget(session, current_user.id, current_month_str)
    budget_out = await _build_budget_out(budget, exchange_rates) if budget else None

    ai_summary: str | None = None
    summary_record = None
    try:
        summary_record_result = await session.execute(
            select(models.LedgerMonthlySummary).where(
                models.LedgerMonthlySummary.user_id == current_user.id,
                models.LedgerMonthlySummary.month == current_month_str,
            )
        )
        summary_record = summary_record_result.scalar_one_or_none()
        if summary_record and summary_record.summary:
            ai_summary = summary_record.summary
    except SQLAlchemyError as error:
        logger.warning(f"读取记账月度总结失败: {error}")

    ledger_note_id: int | None = None
    note_result = await session.execute(_get_ledger_note_for_month(current_user.id, current_month_str))
    ledger_note = note_result.scalar_one_or_none()
    changed = False
    if ledger_note:
        ledger_note_id = ledger_note.id
        note_summary = ledger_note.ai_summary
        record_summary = summary_record.summary if summary_record else None
        if note_summary and record_summary and note_summary != record_summary:
            note_updated = ledger_note.updated_at or ledger_note.created_at
            record_updated = summary_record.updated_at or summary_record.created_at
            if note_updated and record_updated and note_updated > record_updated:
                summary_record.summary = note_summary
                summary_record.updated_at = models.utc_now()
                ai_summary = note_summary
                changed = True
            else:
                ledger_note.ai_summary = record_summary
                ai_summary = record_summary
                changed = True
        elif record_summary and not note_summary:
            ledger_note.ai_summary = record_summary
            ai_summary = record_summary
            changed = True
        elif note_summary and not record_summary:
            if summary_record:
                summary_record.summary = note_summary
                summary_record.updated_at = models.utc_now()
            else:
                last_entry_at = (
                    max(entry.updated_at or entry.created_at for entry in current_month_entries)
                    if current_month_entries
                    else None
                )
                summary_record = models.LedgerMonthlySummary(
                    user_id=current_user.id,
                    month=current_month_str,
                    summary=note_summary,
                    last_entry_at=last_entry_at,
                )
                session.add(summary_record)
            ai_summary = note_summary
            changed = True
        elif note_summary and not ai_summary:
            ai_summary = note_summary

    if changed:
        await session.commit()
    
    return schemas.LedgerStatisticsResponse(
        current_month=current_month_str,
        daily_data=daily_data,
        monthly_data=monthly_data,
        yearly_data=yearly_data,
        yearly_totals=yearly_totals,
        category_stats=category_stats,
        current_month_total=current_month_total,
        last_month_total=last_month_total,
        month_diff=month_diff,
        month_diff_percent=month_diff_percent,
        ai_summary=ai_summary,
        ledger_note_id=ledger_note_id,
        budget=budget_out,
    )


@router.get("/images/{filename}")
async def get_ledger_image(
    filename: str,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """按文件名读取记账原图或缩略图，只能读自己名下的图片。

    必须定义在 /{ledger_id} 之前，否则会被当成 ledger_id 解析。
    """
    safe_name = Path(filename).name
    if not safe_name or safe_name != filename:
        raise HTTPException(status_code=400, detail="非法文件名")

    result = await session.execute(
        select(models.LedgerEntry).where(
            models.LedgerEntry.user_id == current_user.id,
            or_(
                models.LedgerEntry.image_path.endswith(safe_name),
                models.LedgerEntry.image_thumb_path.endswith(safe_name),
            ),
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=404, detail="图片不存在")

    for candidate in (entry.image_path, entry.image_thumb_path):
        if candidate and Path(candidate).name == safe_name and Path(candidate).exists():
            return FileResponse(candidate)

    raise HTTPException(status_code=404, detail="图片不存在")


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
        # 验证分类是否在固定列表中
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

    # 连带删除原图与缩略图（按产品决策：删账即删图）
    for path in (entry.image_path, entry.image_thumb_path):
        if not path:
            continue
        try:
            Path(path).unlink(missing_ok=True)
        except Exception as exc:  # 删文件失败不影响删除记录
            logger.warning(f"删除记账图片失败 {path}: {exc}")

    await session.delete(entry)
    await session.commit()
    return {"message": "账本条目已删除"}

