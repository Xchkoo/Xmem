import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    user_name: Optional[str] = None


class UserOut(UserBase):
    id: int
    user_name: Optional[str] = None
    created_at: dt.datetime

    class Config:
        orm_mode = True


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class NoteBase(BaseModel):
    body_md: str
    images: Optional[List[str]] = None  # 图片URL列表
    files: Optional[List[dict]] = None  # 文件信息列表
    attachment_url: Optional[str] = None


class NoteCreate(NoteBase):
    pass


class NoteOut(NoteBase):
    id: int
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        orm_mode = True


class LedgerCreate(BaseModel):
    text: Optional[str] = None  # 文本输入，如果提供图片则可以为空


class LedgerUpdate(BaseModel):
    """更新账本条目的请求模型"""
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    raw_text: Optional[str] = None
    event_time: Optional[dt.datetime] = None


class LedgerOut(BaseModel):
    id: int
    raw_text: str
    amount: Optional[float]
    currency: str
    category: Optional[str]
    merchant: Optional[str]
    event_time: Optional[dt.datetime]
    meta: Optional[dict]
    status: str  # pending, processing, completed, failed
    task_id: Optional[str] = None
    created_at: dt.datetime
    updated_at: Optional[dt.datetime] = None

    class Config:
        orm_mode = True


class TodoCreate(BaseModel):
    title: str


class TodoOut(BaseModel):
    id: int
    title: str
    completed: bool
    created_at: dt.datetime

    class Config:
        orm_mode = True


class DashboardSummary(BaseModel):
    total_amount: float = 0
    latest_notes: List[NoteOut] = []
    latest_ledgers: List[LedgerOut] = []
    todos: List[TodoOut] = []

