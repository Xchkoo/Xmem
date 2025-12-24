from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .. import models, schemas
from ..auth import create_access_token, verify_password, get_current_user
from ..db import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut)
async def register(payload: schemas.UserCreate, session: AsyncSession = Depends(get_session)):
    # 将邮箱转换为小写，确保数据库中统一存储小写邮箱
    email_lower = payload.email.lower()
    
    exists = await session.execute(select(models.User).where(models.User.email == email_lower))
    if exists.scalars().first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 前端已加密，直接存储
    user = models.User(
        email=email_lower,
        user_name=payload.user_name,
        hashed_password=payload.password
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
async def login(payload: schemas.UserCreate, session: AsyncSession = Depends(get_session)):
    # 将邮箱转换为小写，确保与数据库中的小写邮箱匹配
    email_lower = payload.email.lower()
    
    result = await session.execute(select(models.User).where(models.User.email == email_lower))
    user = result.scalars().first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
async def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
async def change_password(
    payload: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # 验证旧密码
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    # 更新密码（前端已加密）
    current_user.hashed_password = payload.new_password
    await session.commit()
    return {"message": "密码修改成功"}

