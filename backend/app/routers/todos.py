from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/", response_model=list[schemas.TodoOut])
async def list_todos(
    session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)
):
    result = await session.execute(
        select(models.Todo)
        .where(models.Todo.user_id == current_user.id)
        .order_by(models.Todo.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=schemas.TodoOut)
async def create_todo(
    payload: schemas.TodoCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    todo = models.Todo(user_id=current_user.id, title=payload.title)
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return todo


@router.patch("/{todo_id}", response_model=schemas.TodoOut)
async def toggle_todo(
    todo_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Todo).where(models.Todo.id == todo_id, models.Todo.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    todo.completed = not todo.completed
    await session.commit()
    await session.refresh(todo)
    return todo


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Todo).where(models.Todo.id == todo_id, models.Todo.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    await session.delete(todo)
    await session.commit()
    return {"ok": True}

