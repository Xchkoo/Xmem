#!/usr/bin/env python3
"""确保数据库存在，如果不存在则创建"""
import asyncio
import asyncpg
from urllib.parse import urlparse, quote_plus
from app.config import settings


async def ensure_database():
    """确保数据库存在，如果不存在则创建"""
    # 解析数据库 URL
    db_url = settings.database_url
    # 移除 asyncpg 驱动前缀（如果存在）
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    parsed = urlparse(db_url)
    
    # 提取数据库名
    db_name = parsed.path.lstrip("/")
    if not db_name:
        print("错误: 无法从 DATABASE_URL 中提取数据库名")
        return False
    
    # 构建连接到 postgres 数据库的 URL（用于创建目标数据库）
    # 使用 quote_plus 处理密码中的特殊字符
    username = quote_plus(parsed.username or "postgres")
    password = quote_plus(parsed.password or "")
    hostname = parsed.hostname or "localhost"
    port = parsed.port or 5432
    
    if password:
        admin_url = f"postgresql://{username}:{password}@{hostname}:{port}/postgres"
    else:
        admin_url = f"postgresql://{username}@{hostname}:{port}/postgres"
    
    try:
        # 连接到 postgres 数据库
        conn = await asyncpg.connect(admin_url)
        
        # 检查数据库是否存在
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        
        if exists:
            print(f"数据库 '{db_name}' 已存在")
            await conn.close()
            return True
        
        # 创建数据库
        print(f"创建数据库 '{db_name}'...")
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        print(f"✓ 数据库 '{db_name}' 创建成功")
        await conn.close()
        return True
        
    except Exception as e:
        print(f"错误: 无法创建数据库 '{db_name}': {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(ensure_database())
    if not success:
        exit(1)

