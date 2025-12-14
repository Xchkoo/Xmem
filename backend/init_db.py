#!/usr/bin/env python3
"""初始化数据库表结构"""
import asyncio
from app.db import engine, Base
from app import models


async def init_db():
    """创建所有数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表结构创建完成")


if __name__ == "__main__":
    asyncio.run(init_db())

