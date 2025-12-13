from datetime import datetime, timezone
import logging
import json
import re
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..celery_app import celery_app
from ..config import settings
from .. import models


logger = logging.getLogger(__name__)

# 创建同步数据库引擎用于 Celery 任务
sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_db_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def parse_utc_time(time_str: str | None) -> str | None:
    """
    验证并解析 UTC 时间字符串
    
    Args:
        time_str: 时间字符串，格式应为 YYYY-MM-DDTHH:MM:SSZ
        
    Returns:
        如果时间字符串有效，返回格式化的 UTC 时间字符串；否则返回 None
    """
    if not time_str or not isinstance(time_str, str):
        return None
    
    # 移除首尾空白
    time_str = time_str.strip()
    
    # 严格匹配 UTC 时间格式：YYYY-MM-DDTHH:MM:SSZ
    # 例如：2024-01-15T10:30:45Z
    utc_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
    
    if not re.match(utc_pattern, time_str):
        logger.warning(f"时间格式不符合 UTC 标准格式 (YYYY-MM-DDTHH:MM:SSZ): {time_str}")
        return None
    
    # 尝试解析时间字符串
    try:
        # 使用 strptime 解析，Z 表示 UTC
        dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
        # 确保时区是 UTC
        dt = dt.replace(tzinfo=timezone.utc)
        # 验证并格式化返回
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.warning(f"无法解析时间字符串 {time_str}: {str(e)}")
        return None


@celery_app.task(name="ledger.merge_and_analyze")
def merge_text_and_analyze(ocr_text: str, original_text: str | None = None, entry_id: int | None = None) -> dict:
    """
    Celery 任务：合并 OCR 文本和原始文本，然后进行分析
    
    Args:
        ocr_text: OCR 提取的文本
        original_text: 原始文本（可选）
        
    Returns:
        LLM 分析结果，包含合并后的文本（在 meta 中）
    """
    # 合并文本
    if original_text:
        processed_text = "备注remark: "" + original_text + """
        merged_text = processed_text + "\n" + ocr_text
    else:
        merged_text = ocr_text
    
    # 调用分析任务
    result = analyze_ledger_text(merged_text)
    
    # 确保 meta 中包含合并后的文本
    if "meta" not in result:
        result["meta"] = {}
    result["meta"]["raw_text"] = merged_text
    
    # 如果提供了 entry_id，也包含在结果中，用于后续更新
    if entry_id is not None:
        result["_entry_id"] = entry_id
        result["_original_text"] = original_text
    
    return result


@celery_app.task(name="ledger.wrap_analyze_text")
def wrap_analyze_text_with_entry_id(text: str, entry_id: int) -> dict:
    """
    Celery 任务：分析文本并添加 entry_id
    
    Args:
        text: 要分析的文本
        entry_id: 账本条目 ID
        
    Returns:
        LLM 分析结果，包含 entry_id
    """
    result = analyze_ledger_text(text)
    result["_entry_id"] = entry_id
    return result


@celery_app.task(name="ledger.analyze_text")
def analyze_ledger_text(text: str) -> dict:
    """
    Celery 任务：分析账本文本
    这个任务会在后台异步执行，调用 LLM 服务分析文本
    
    Args:
        text: 要分析的文本
        
    Returns:
        分析结果字典，包含 amount, currency, category, merchant, event_time, meta
    """
    try:
        llm_provider = settings.llm_provider if settings.llm_provider else None
        if not llm_provider:
            raise ValueError("LLM_PROVIDER 未配置，无法调用")
        
        #API提供商是Deepseek的实现
        if llm_provider == "deepseek":        
            logger.info(f"开始 LLM 分析任务，文本长度: {len(text)}")
            
            # 调用 Deepseek 进行分析
            # 获取 API 配置，如果没有配置则使用默认的 DeepSeek API
            api_key = settings.llm_api_key if settings.llm_api_key else None
            base_url = settings.llm_api_url if settings.llm_api_url else "https://api.deepseek.com"
            
            if not api_key:
                raise ValueError("LLM_API_KEY 未配置，无法调用")
            
            # 创建客户端（DeepSeek API兼容 OpenAI）
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            

            # 导入分类常量
            from ..constants import LEDGER_CATEGORIES
            
            hint = f"""
你是记账助手。请把下面用户输入的消费或收款信息解析成 JSON，不要解释，直接输出 JSON，字段如下：
- amount: 金额数字，数字类型
- currency: 货币单位，字符串，如 CNY、USD
- category: 消费类别，必须是以下固定分类之一：{', '.join(LEDGER_CATEGORIES)}。请根据消费内容选择最合适的分类，如果都不合适则选择"其他"。
- description: 用户原文文本
- event_time: 消费时间,没有就不填写,有则填写utc时间格式即YYYY-MM-DDTHH:MM:SSZ
"""
            
            # 调用 DeepSeek API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": hint},
                    {"role": "user", "content": text},
                ],
                stream=False
            )
            
            # 解析返回的 JSON
            response_content = response.choices[0].message.content.strip()
            
            # 尝试提取 JSON（可能包含 markdown 代码块）
            if response_content.startswith("```"):
                # 移除 markdown 代码块标记
                lines = response_content.split("\n")
                response_content = "\n".join(lines[1:-1]) if len(lines) > 2 else response_content
            
            # 解析 JSON
            try:
                llm_result = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"解析 LLM 返回的 JSON 失败: {response_content}, 错误: {str(e)}")
                raise ValueError(f"LLM 返回的 JSON 格式无效: {str(e)}")
            
            # 处理 event_time：验证是否为严格的 UTC 时间格式
            llm_event_time = llm_result.get("event_time")
            validated_event_time = parse_utc_time(llm_event_time)
            
            # 如果验证失败或为空，使用当前 UTC 时间
            if validated_event_time is None:
                validated_event_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if llm_event_time:
                    logger.info(f"LLM 返回的时间格式无效 ({llm_event_time})，使用当前 UTC 时间: {validated_event_time}")
            
            # 验证并修正分类
            category = llm_result.get("category", "其他")
            if category not in LEDGER_CATEGORIES:
                # 如果 AI 返回的分类不在固定列表中，使用"其他"
                logger.warning(f"AI 返回的分类 '{category}' 不在固定列表中，使用'其他'")
                category = "其他"
            
            # 映射字段到需要的格式
            result = {
                "amount": llm_result.get("amount"),
                "currency": llm_result.get("currency", "CNY"),
                "category": category,
                "merchant": None,  # 可以从 description 中提取，暂时留空
                "event_time": validated_event_time,
                "meta": {
                    "model": "deepseek-chat",
                    "text_length": len(text),
                    "description": llm_result.get("description", text),
                },
            }

            logger.info(f"LLM 分析任务完成")
            return result
        # elif:
            #其他API提供商的实现 暂时留空  
        else:
            raise ValueError(f"不支持的 LLM 提供商: {llm_provider}")
    except Exception as e:
        logger.error(f"LLM 分析任务失败: {str(e)}")
        raise


@celery_app.task(name="ledger.update_entry")
def update_ledger_entry(
    ai_result: dict,
    entry_id: int | None = None,
    original_text: str | None = None,
) -> dict:
    """
    Celery 任务：更新账本条目
    
    Args:
        ai_result: LLM 分析结果（可能包含 _entry_id 和 _original_text）
        entry_id: 账本条目 ID（如果不在 ai_result 中）
        original_text: 原始文本（用于合并文本的情况，如果不在 ai_result 中）
        
    Returns:
        更新后的条目信息
    """
    # 如果 ai_result 中包含 _entry_id，优先使用
    if "_entry_id" in ai_result:
        entry_id = ai_result.pop("_entry_id")
        if "_original_text" in ai_result:
            original_text = ai_result.pop("_original_text")
    
    if not entry_id:
        raise ValueError("entry_id 未提供")
    
    session: Session = SyncSessionLocal()
    try:
        logger.info(f"开始更新账本条目 {entry_id}")
        
        # 获取条目
        entry = session.query(models.LedgerEntry).filter(models.LedgerEntry.id == entry_id).first()
        if not entry:
            raise ValueError(f"账本条目 {entry_id} 不存在")
        
        # 如果有原始文本，需要合并
        if original_text and ai_result.get("meta", {}).get("description"):
            # 检查是否需要合并（OCR + 原始文本的情况）
            pass  # 已在 analyze_ledger_text 中处理
        
        # 解析 event_time 字符串为 datetime
        event_time_str = ai_result.get("event_time")
        event_time = None
        if event_time_str:
            try:
                event_time = datetime.strptime(event_time_str, "%Y-%m-%dT%H:%M:%SZ")
                # 转换为 naive datetime（用于数据库存储）
                event_time = event_time.replace(tzinfo=None)
            except ValueError as e:
                logger.warning(f"无法解析 event_time {event_time_str}: {str(e)}")
                event_time = datetime.utcnow()
        
        # 导入分类常量并验证
        from ..constants import LEDGER_CATEGORIES
        
        # 更新条目
        entry.amount = ai_result.get("amount")
        entry.currency = ai_result.get("currency", "CNY")
        
        # 验证并修正分类
        category = ai_result.get("category")
        if category and category not in LEDGER_CATEGORIES:
            logger.warning(f"AI 返回的分类 '{category}' 不在固定列表中，使用'其他'")
            category = "其他"
        entry.category = category
        entry.merchant = ai_result.get("merchant")
        entry.event_time = event_time or datetime.utcnow()
        entry.meta = ai_result.get("meta")
        entry.status = "completed"
        
        # 更新 raw_text（优先使用 meta 中的 raw_text，否则使用 description）
        meta = ai_result.get("meta", {})
        if meta.get("raw_text"):
            entry.raw_text = meta["raw_text"]
        elif meta.get("description") and not entry.raw_text:
            entry.raw_text = meta["description"]
        
        session.commit()
        session.refresh(entry)
        
        logger.info(f"账本条目 {entry_id} 更新完成")
        return {"status": "completed", "entry_id": entry_id}
    except Exception as e:
        logger.error(f"更新账本条目失败: {str(e)}")
        session.rollback()
        # 更新状态为失败
        try:
            entry = session.query(models.LedgerEntry).filter(models.LedgerEntry.id == entry_id).first()
            if entry:
                entry.status = "failed"
                session.commit()
        except Exception as update_error:
            logger.error(f"更新失败状态时出错: {str(update_error)}")
        raise
    finally:
        session.close()

