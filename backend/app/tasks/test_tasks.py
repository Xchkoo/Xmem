from datetime import datetime, timezone
import time
from ..celery_app import celery_app


@celery_app.task(name="test.connection")
def test_connection():
    """
    测试 Celery 和 Redis 连接
    返回连接状态信息
    """
    return {
        "status": "success",
        "message": "Celery 和 Redis 连接正常！",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_time": time.time()
    }


@celery_app.task(name="test.echo")
def test_echo(message: str = "Hello, Celery!"):
    """
    简单的回显测试任务
    用于验证任务执行和结果返回
    """
    return {
        "echo": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "received_at": time.time()
    }

