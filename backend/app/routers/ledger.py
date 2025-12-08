from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user
from ..services import ledger_ai

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/", response_model=list[schemas.LedgerOut])
async def list_ledgers(
    session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)
):
    result = await session.execute(
        select(models.LedgerEntry)
        .where(models.LedgerEntry.user_id == current_user.id)
        .order_by(models.LedgerEntry.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=schemas.LedgerOut)
async def create_ledger(
    payload: schemas.LedgerCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    ai_result = await ledger_ai.analyze(payload.text)
    entry = models.LedgerEntry(
        user_id=current_user.id,
        raw_text=payload.text,
        amount=ai_result.get("amount"),
        currency=ai_result.get("currency", "CNY"),
        category=ai_result.get("category"),
        merchant=ai_result.get("merchant"),
        event_time=ai_result.get("event_time"),
        meta=ai_result.get("meta"),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.get("/summary")
async def summary(
    session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)
):
    total_amount = await session.execute(
        select(func.coalesce(func.sum(models.LedgerEntry.amount), 0)).where(
            models.LedgerEntry.user_id == current_user.id
        )
    )
    total = total_amount.scalar() or 0
    recent = await session.execute(
        select(models.LedgerEntry)
        .where(models.LedgerEntry.user_id == current_user.id)
        .order_by(models.LedgerEntry.created_at.desc())
        .limit(5)
    )
    return {"total_amount": total, "recent": recent.scalars().all()}

