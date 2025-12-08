import datetime as dt
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import settings
from . import models, schemas
from .db import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(password: str, hashed: str) -> bool:
    """前端已加密，直接比较"""
    return password == hashed


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

