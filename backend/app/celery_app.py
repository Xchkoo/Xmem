from celery import Celery
from .config import settings

# 创建 Celery 应用
celery_app = Celery(
    "xmem_backend",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分钟超时
    task_soft_time_limit=25 * 60,  # 25 分钟软超时
    # 自动发现任务
    imports=("app.tasks.ledger_tasks", "app.tasks.test_tasks", "app.tasks.ocr_tasks"),
)