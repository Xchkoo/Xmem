#!/usr/bin/env python3
"""
快速检查 Celery 和 Redis 配置
"""

import sys
import os

def check_redis():
    """检查 Redis 连接"""
    print("检查 Redis 连接...")
    try:
        import redis
        from app.config import settings
        
        print(f"  Redis URL: {settings.redis_url}")
        
        # 尝试连接
        r = redis.from_url(settings.redis_url)
        result = r.ping()
        if result:
            print("  ✓ Redis 连接正常")
            return True
        else:
            print("  ✗ Redis ping 失败")
            return False
    except ImportError:
        print("  ✗ redis 模块未安装")
        return False
    except Exception as e:
        print(f"  ✗ Redis 连接失败: {e}")
        print("  请确保 Redis 正在运行")
        return False

def check_celery_app():
    """检查 Celery 应用配置"""
    print("\n检查 Celery 应用配置...")
    try:
        from app.celery_app import celery_app
        
        print(f"  Celery 应用名称: {celery_app.main}")
        print(f"  Broker URL: {celery_app.conf.broker_url}")
        print(f"  Backend URL: {celery_app.conf.result_backend}")
        
        # 检查注册的任务
        registered_tasks = list(celery_app.tasks.keys())
        print(f"  注册的任务数量: {len(registered_tasks)}")
        
        # 显示任务
        if registered_tasks:
            print("  任务:")
            for task in registered_tasks:
                print(f"    - {task}")
        else:
            print("  ⚠ 未找到任务，请检查任务是否已注册")
        
        print("  ✓ Celery 应用配置正常")
        return True
    except Exception as e:
        print(f"  ✗ Celery 应用配置错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("Celery 和 Redis 配置检查")
    print("=" * 50)
    print()
    
    redis_ok = check_redis()
    celery_ok = check_celery_app()
    
    print()
    print("=" * 50)
    if redis_ok and celery_ok:
        print("✓ 配置检查通过")
        print()
        print("下一步:")
        print("  1. 启动 Celery Worker: cd backend && .\\run-celery.ps1")
        print("  2. 运行测试: uv run python test_celery.py")
    else:
        print("✗ 配置检查失败")
        print()
        if not redis_ok:
            print("请先解决 Redis 连接问题")
        if not celery_ok:
            print("请检查 Celery 配置")
    print("=" * 50)

if __name__ == "__main__":
    main()

