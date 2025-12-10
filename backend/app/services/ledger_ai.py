import asyncio
from datetime import datetime, timezone
from ..tasks.ledger_tasks import analyze_ledger_text



async def analyze(text: str, use_celery: bool = True) -> dict:
    """
    分析账本文本
    
    Args:
        text: 要分析的文本
        use_celery: 是否使用 Celery 异步任务队列（默认 True）
        
    Returns:
        分析结果字典
    """
    if use_celery:
        # 使用 Celery 异步任务队列
        # 使用 .delay() 提交任务到队列
        task_result = analyze_ledger_text.delay(text)
        # 使用 asyncio.to_thread 在后台线程中等待结果，避免阻塞事件循环
        result = await asyncio.to_thread(task_result.get, timeout=300)  # 5 分钟超时
        return result
    else:
        # 同步调用（用于测试或不需要队列的场景）
        return analyze_ledger_text(text)