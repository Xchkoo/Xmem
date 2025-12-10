#!/bin/bash
# 启动 Celery Worker
# 需要先启动 Redis 服务

# 设置工作目录
cd "$(dirname "$0")"

# 启动 Celery worker
# -A 指定 Celery 应用
# --loglevel=info 设置日志级别
# 使用 uv run 在 uv 管理的虚拟环境中运行
uv run celery -A app.celery_app:celery_app worker --loglevel=info

