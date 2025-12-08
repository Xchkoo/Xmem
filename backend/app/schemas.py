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
    body: str
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
    text: str


class LedgerOut(BaseModel):
    id: int
    raw_text: str
    amount: Optional[float]
    currency: str
    category: Optional[str]
    merchant: Optional[str]
    event_time: Optional[dt.datetime]
    meta: Optional[dict]
    created_at: dt.datetime

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

