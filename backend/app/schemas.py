import datetime as dt
from typing import Optional, List, Literal

from pydantic import BaseModel, EmailStr


def _encode_datetime_utc(value: dt.datetime | None):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    else:
        value = value.astimezone(dt.timezone.utc)
    encoded = value.isoformat()
    if encoded.endswith("+00:00"):
        encoded = encoded[:-6] + "Z"
    return encoded


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
        json_encoders = {dt.datetime: _encode_datetime_utc}


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class NoteBase(BaseModel):
    body_md: str
    images: Optional[list[str]] = None


class NoteFileOut(BaseModel):
    name: str
    url: str
    size: int


class NoteCreate(NoteBase):
    files: Optional[list[NoteFileOut]] = None
    ai_summary: Optional[str] = None
    is_ledger_note: Optional[bool] = None
    ledger_month: Optional[str] = None


class NoteOut(NoteBase):
    id: int
    ai_summary: Optional[str] = None
    is_ledger_note: bool = False
    ledger_month: Optional[str] = None
    is_pinned: bool = False
    is_shared: bool = False
    share_uuid: Optional[str] = None
    created_at: dt.datetime
    updated_at: dt.datetime
    files: Optional[list[NoteFileOut]] = None

    class Config:
        from_attributes = True
        json_encoders = {dt.datetime: _encode_datetime_utc}


class NoteShareLinkOut(BaseModel):
    note_uuid: str
    share_user_id: int
    share_url: str


class NoteShareToggleIn(BaseModel):
    is_shared: bool


class NoteShareStatusOut(BaseModel):
    is_shared: bool
    note_uuid: Optional[str] = None
    share_user_id: int
    share_url: Optional[str] = None


class NoteAiSummaryOut(BaseModel):
    summary: str


class NoteAiTodosOut(BaseModel):
    todos: list["TodoOut"]


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatContextNote(BaseModel):
    id: int
    body_md: str


class ChatContextLedger(BaseModel):
    id: int
    raw_text: str
    amount: Optional[float] = None
    category: Optional[str] = None


class ChatContext(BaseModel):
    notes: list[ChatContextNote] = []
    ledgers: list[ChatContextLedger] = []


class ChatRequest(BaseModel):
    messages: list[ChatMessageIn]
    context: Optional[ChatContext] = None


class ChatResponse(BaseModel):
    reply: str


class NoteExportEstimateIn(BaseModel):
    export_type: str
    note_ids: Optional[list[int]] = None
    include_all: bool = False


class NoteExportEstimateOut(BaseModel):
    estimated_size: int


class NoteExportCreateIn(BaseModel):
    export_type: str
    note_ids: Optional[list[int]] = None
    include_all: bool = False


class NoteExportJobOut(BaseModel):
    id: int
    export_type: str
    status: str
    note_ids: Optional[list[int]] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    checksum_sha256: Optional[str] = None
    progress: int = 0
    error_message: Optional[str] = None
    created_at: dt.datetime
    updated_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {dt.datetime: _encode_datetime_utc}


class SharedUserOut(BaseModel):
    id: int
    email: EmailStr
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class NoteShareOut(NoteBase):
    id: int
    ai_summary: Optional[str] = None
    is_pinned: bool = False
    created_at: dt.datetime
    updated_at: dt.datetime
    files: Optional[list[NoteFileOut]] = None
    share_user: SharedUserOut
    can_edit: bool = False

    class Config:
        from_attributes = True
        json_encoders = {dt.datetime: _encode_datetime_utc}


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
    # 原始截图（证据）访问路径；由 models.LedgerEntry 的 property 提供
    image_url: Optional[str] = None
    image_thumb_url: Optional[str] = None
    created_at: dt.datetime
    updated_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {dt.datetime: _encode_datetime_utc}


class TodoCreate(BaseModel):
    title: str
    group_id: Optional[int] = None
    is_ai_generated: bool = False


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None


class TodoOut(BaseModel):
    id: int
    title: str
    completed: bool
    is_pinned: bool = False
    is_ai_generated: bool = False
    group_id: Optional[int] = None
    created_at: dt.datetime
    # 组的子待办列表（如果这是组标题）
    group_items: Optional[list["TodoOut"]] = None

    class Config:
        from_attributes = True
        # 允许延迟评估，解决循环引用
        json_encoders = {dt.datetime: _encode_datetime_utc}


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


class YearlyStats(BaseModel):
    """年度统计数据"""
    year: int
    amount: float
    count: int


class DailyStats(BaseModel):
    """日度统计数据"""
    date: str  # YYYY-MM-DD
    amount: float
    count: int


class CategoryStats(BaseModel):
    """分类统计数据"""
    category: str
    amount: float
    count: int
    percentage: float


class LedgerBudgetIn(BaseModel):
    month: str
    amount: float
    currency: str = "CNY"


class LedgerBudgetOut(BaseModel):
    month: str
    amount: float
    currency: str
    amount_cny: Optional[float] = None


class LedgerMonthlySummaryOut(BaseModel):
    """记账月度总结响应"""
    summary: str


class LedgerStatisticsResponse(BaseModel):
    """记账统计响应"""
    current_month: str
    daily_data: List[DailyStats]
    monthly_data: List[MonthlyStats]  # 近6个月
    yearly_data: List[MonthlyStats]  # 全年12个月
    yearly_totals: List[YearlyStats]  # 近几年总额
    category_stats: List[CategoryStats]  # 分类统计
    current_month_total: float
    last_month_total: float
    month_diff: float
    month_diff_percent: float
    ai_summary: Optional[str] = None
    ledger_note_id: Optional[int] = None
    budget: Optional[LedgerBudgetOut] = None
