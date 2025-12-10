#!/usr/bin/env python3
"""
Celery 连接测试脚本
用于验证 Celery Worker 和 Redis 是否正常工作
"""

import sys
from app.tasks.test_tasks import test_connection, test_echo


def test_celery():
    """测试 Celery 连接"""
    print("=" * 50)
    print("Celery 连接测试")
    print("=" * 50)
    print()
    
    # 测试 1: 简单连接测试
    print("1. 测试连接任务...")
    try:
        result = test_connection.delay()
        print(f"   ✓ 任务已提交")
        print(f"   任务 ID: {result.id}")
        print(f"   初始状态: {result.state}")
        print()
        print("   正在等待 Worker 处理任务...")
        print("   (如果长时间无响应，请检查 Celery Worker 是否运行)")
        print()
        
        # 等待结果，添加更详细的超时处理
        import time
        start_time = time.time()
        try:
            task_result = result.get(timeout=15)
            elapsed = time.time() - start_time
            print(f"   ✓ 任务执行成功 (耗时: {elapsed:.2f}秒)")
            print(f"   最终状态: {result.state}")
            print(f"   结果: {task_result}")
            print()
        except Exception as timeout_error:
            elapsed = time.time() - start_time
            print(f"   ✗ 等待超时 (已等待 {elapsed:.2f}秒)")
            print(f"   当前任务状态: {result.state}")
            print(f"   错误: {timeout_error}")
            print()
            print("   可能的原因:")
            print("   1. Celery Worker 未运行 - 请运行: cd backend && .\\run-celery.ps1")
            print("   2. Redis 未运行 - 请检查: redis-cli ping")
            print("   3. 任务未注册 - 请检查 Worker 日志中是否有任务注册信息")
            print("   4. REDIS_URL 配置错误 - 请检查 .env 文件")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("请检查:")
        print("  1. Redis 是否正在运行 (redis-cli ping)")
        print("  2. Celery Worker 是否正在运行 (运行 run-celery.ps1 或 run-celery.sh)")
        print("  3. REDIS_URL 环境变量是否正确配置")
        return False
    
    # 测试 2: 回显测试
    print("2. 测试回显任务...")
    try:
        test_message = "测试消息 - Celery 工作正常！"
        result2 = test_echo.delay(test_message)
        print(f"   ✓ 任务已提交")
        print(f"   任务 ID: {result2.id}")
        print("   正在等待结果...")
        
        import time
        start_time = time.time()
        task_result2 = result2.get(timeout=15)
        elapsed = time.time() - start_time
        print(f"   ✓ 任务执行成功 (耗时: {elapsed:.2f}秒)")
        print(f"   回显结果: {task_result2['echo']}")
        print(f"   时间戳: {task_result2['timestamp']}")
        print()
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False
    
    print("=" * 50)
    print("✓ 所有测试通过！")
    print("=" * 50)
    print()
    print("Celery 和 Redis 连接正常，可以正常使用。")
    return True


if __name__ == "__main__":
    try:
        success = test_celery()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

