from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[schemas.NoteOut])
async def list_notes(
    session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)
):
    result = await session.execute(
        select(models.Note).where(models.Note.user_id == current_user.id).order_by(models.Note.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=schemas.NoteOut)
async def create_note(
    payload: schemas.NoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    note = models.Note(user_id=current_user.id, body=payload.body, attachment_url=payload.attachment_url)
    session.add(note)
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

