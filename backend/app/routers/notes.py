import os
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..utils.file_utils import save_uploaded_img, save_uploaded_file

router = APIRouter(prefix="/notes", tags=["notes"])

# 文件上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
IMAGE_DIR = UPLOAD_DIR / "images"
FILE_DIR = UPLOAD_DIR / "files"
IMAGE_DIR.mkdir(exist_ok=True)
FILE_DIR.mkdir(exist_ok=True)

# 文件大小限制：5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


def clean_markdown_for_search(markdown_text: str) -> str:
    """移除 markdown 中的图片和链接语法，只保留纯文本用于搜索"""
    if not markdown_text:
        return ""
    
    text = markdown_text
    # 移除图片语法: ![alt](url) - 完全移除，只保留 alt 文本（如果有）
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    # 移除链接语法: [text](url) - 只保留链接文本
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    return text


@router.get("", response_model=list[schemas.NoteOut])
async def list_notes(
    q: str | None = None,
    session: AsyncSession = Depends(get_session), 
    current_user: models.User = Depends(get_current_user)
):
    """
    获取所有笔记 如果有搜索关键词则过滤
    Args:
        q: 搜索关键词
    Returns:
        list[schemas.NoteOut]: 笔记列表
    """
    # 先获取所有笔记
    query = select(models.Note).where(models.Note.user_id == current_user.id)
    query = query.order_by(models.Note.created_at.desc())
    result = await session.execute(query)
    notes = result.scalars().all()
    
    # 如果有搜索关键词，在 Python 层面过滤（排除 markdown 图片和链接语法）
    if q is not None and q.strip():
        q_trimmed = q.strip().lower()
        filtered_notes = []
        for note in notes:
            # 清理 markdown 语法后搜索
            cleaned_text = clean_markdown_for_search(note.body_md or "")
            if q_trimmed in cleaned_text.lower():
                filtered_notes.append(note)
        return filtered_notes
    
    return notes


@router.post("", response_model=schemas.NoteOut)
async def create_note(
    payload: schemas.NoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    note = models.Note(
        user_id=current_user.id,
        body_md=payload.body_md,
        images=payload.images,
        files=payload.files,
        attachment_url=payload.attachment_url
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    """上传图片（暂不校验大小）"""
    # 使用通用函数保存图片文件
    file_path = await save_uploaded_img(file, IMAGE_DIR)
    
    # 从完整路径中提取文件名
    file_name = Path(file_path).name
    
    # 返回URL（使用相对路径，前端会拼接baseURL）
    return {"url": f"/notes/files/images/{file_name}"}


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    """上传文件（校验大小）"""
    # 使用通用函数保存文件（包含大小验证）
    original_name = file.filename or "file"
    file_path, content = await save_uploaded_file(file, FILE_DIR, max_size=MAX_FILE_SIZE, default_ext=Path(original_name).suffix)
    
    # 从完整路径中提取文件名
    file_name = Path(file_path).name
    
    # 返回文件信息（使用相对路径，前端会拼接baseURL）
    return {
        "name": original_name,
        "url": f"/notes/files/files/{file_name}",
        "size": len(content)
    }




@router.patch("/{note_id}", response_model=schemas.NoteOut)
async def update_note(
    note_id: int,
    payload: schemas.NoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    note.body_md = payload.body_md
    note.images = payload.images
    note.files = payload.files
    if payload.attachment_url:
        note.attachment_url = payload.attachment_url
    
    await session.commit()
    await session.refresh(note)
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    await session.delete(note)
    await session.commit()
    return {"ok": True}

