from datetime import datetime, timezone
from ..celery_app import celery_app


@celery_app.task(name="ledger.analyze_text")
def analyze_ledger_text(text: str) -> dict:
    """
    Celery 任务：分析账本文本
    这个任务会在后台异步执行，调用 AI 服务分析文本
    
    Args:
        text: 要分析的文本
        
    Returns:
        分析结果字典，包含 amount, currency, category, merchant, event_time, meta
    """
    # TODO: 实现真实的 AI 分析逻辑
    # 这里先返回占位数据，后续可以调用真实的大模型 API
    # 注意：Celery 任务不能是 async 函数，如果需要异步操作，需要在任务内部处理
    
    # 占位实现
    return {
        "amount": None,
        "currency": "CNY",
        "category": "未分类",
        "merchant": None,
        "event_time": datetime.now(timezone.utc),
        "meta": {"model": "celery_task", "text_length": len(text)},
    }

