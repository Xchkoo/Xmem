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
        from_attributes = True


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
    is_pinned: bool = False
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


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
        from_attributes = True


class TodoCreate(BaseModel):
    title: str
    group_id: Optional[int] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None


class TodoOut(BaseModel):
    id: int
    title: str
    completed: bool
    is_pinned: bool = False
    group_id: Optional[int] = None
    created_at: dt.datetime
    # 组的子待办列表（如果这是组标题）
    group_items: Optional[list["TodoOut"]] = None

    class Config:
        from_attributes = True
        # 允许延迟评估，解决循环引用
        json_encoders = {
            dt.datetime: lambda v: v.isoformat() if v else None
        }


class DashboardSummary(BaseModel):
    total_amount: float = 0
    latest_notes: List[NoteOut] = []
    latest_ledgers: List[LedgerOut] = []
    todos: List[TodoOut] = []


class LedgerListResponse(BaseModel):
    """分页的记账列表响应"""
    items: List[LedgerOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class MonthlyStats(BaseModel):
    """月度统计数据"""
    month: str  # YYYY-MM
    amount: float
    count: int


class CategoryStats(BaseModel):
    """分类统计数据"""
    category: str
    amount: float
    count: int
    percentage: float


class LedgerStatisticsResponse(BaseModel):
    """记账统计响应"""
    monthly_data: List[MonthlyStats]  # 近6个月
    yearly_data: List[MonthlyStats]  # 全年12个月
    category_stats: List[CategoryStats]  # 分类统计
    current_month_total: float
    last_month_total: float
    month_diff: float
    month_diff_percent: float
