import os
import asyncio
import datetime as dt
from sqlalchemy import select
from .. import models
from ..db import AsyncSessionLocal
from ..celery_app import celery_app

@celery_app.task
def cleanup_orphan_files():
    """
    清理孤儿文件（未关联笔记且超过24小时）
    """
    # 在同步任务中运行异步逻辑
    asyncio.run(_cleanup_logic())

async def _cleanup_logic():
    async with AsyncSessionLocal() as session:
        # 查找 created_at < 24h ago AND note_id is NULL
        # 注意：created_at 存储的是 naive UTC time
        limit_time = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(hours=24)
        
        stmt = select(models.File).where(
            models.File.note_id.is_(None),
            models.File.created_at < limit_time
        )
        result = await session.execute(stmt)
        files_to_delete = result.scalars().all()
        
        if not files_to_delete:
            return
            
        print(f"Found {len(files_to_delete)} orphan files to cleanup.")
        
        for f in files_to_delete:
            # 删除物理文件
            try:
                if os.path.exists(f.file_path):
                    os.remove(f.file_path)
                    print(f"Deleted file: {f.file_path}")
            except Exception as e:
                print(f"Error deleting file {f.file_path}: {e}")
            
            # 删除数据库记录
            await session.delete(f)
        
        await session.commit()
