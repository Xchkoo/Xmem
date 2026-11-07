import datetime as dt
import os

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .db import Base


def utc_now():
    """返回当前 UTC 时区的 naive datetime 对象（用于数据库存储）"""
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    user_name = Column(String(64), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    ledgers = relationship("LedgerEntry", back_populates="owner", cascade="all, delete-orphan")
    ledger_budgets = relationship("LedgerBudget", back_populates="owner", cascade="all, delete-orphan")
    ledger_monthly_summaries = relationship("LedgerMonthlySummary", back_populates="owner", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="owner", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    body_md = Column(Text, nullable=False)  # Markdown 格式内容
    ai_summary = Column(Text, nullable=True)
    is_ledger_note = Column(Boolean, default=False, nullable=False)
    ledger_month = Column(String(7), nullable=True)
    is_pinned = Column(Boolean, default=False, nullable=False)  # 是否置顶
    is_shared = Column(Boolean, default=False, nullable=False)  # 是否分享
    share_uuid = Column(String(64), unique=True, index=True, nullable=True)  # 分享固定UUID
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now) 

    owner = relationship("User", back_populates="notes")
    managed_files = relationship("File", back_populates="note", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    file_path = Column(String(512), nullable=False)  # 物理路径
    url_path = Column(String(512), nullable=False)   # Web访问路径 (用于匹配)
    file_type = Column(String(16), nullable=False)   # 'image' or 'file'
    created_at = Column(DateTime, default=utc_now)

    owner = relationship("User", backref="uploaded_files")
    note = relationship("Note", back_populates="managed_files")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    raw_text = Column(Text, nullable=False)
    amount = Column(Float, nullable=True)
    currency = Column(String(16), default="CNY")
    category = Column(String(64), nullable=True)
    merchant = Column(String(128), nullable=True)
    event_time = Column(DateTime, nullable=True)
    meta = Column(JSON, nullable=True)
    status = Column(String(16), default="pending", nullable=False)  # pending, processing, completed, failed
    task_id = Column(String(255), nullable=True)  # Celery 任务 ID
    # 原始截图（证据）与缩略图；OCR 文本只作为 AI 输入，不再承担"凭证"角色
    image_path = Column(String(512), nullable=True)
    image_thumb_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="ledgers")

    @property
    def image_url(self) -> str | None:
        """原图访问路径（前端拼 API base 使用）。"""
        return f"/ledger/images/{os.path.basename(self.image_path)}" if self.image_path else None

    @property
    def image_thumb_url(self) -> str | None:
        """缩略图访问路径，没有生成时回落到原图。"""
        path = self.image_thumb_path or self.image_path
        return f"/ledger/images/{os.path.basename(path)}" if path else None


class LedgerBudget(Base):
    __tablename__ = "ledger_budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    month = Column(String(7), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(16), default="CNY", nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="ledger_budgets")


class LedgerMonthlySummary(Base):
    __tablename__ = "ledger_monthly_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    month = Column(String(7), index=True, nullable=False)
    summary = Column(Text, nullable=True)
    last_entry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="ledger_monthly_summaries")


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False, nullable=False)  # 是否置顶
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    group_id = Column(Integer, ForeignKey("todos.id"), nullable=True)  # 组ID，指向组标题待办（自引用）
    created_at = Column(DateTime, default=utc_now)

    owner = relationship("User", back_populates="todos")
    # 自引用关系：组的子待办列表（一对多关系）
    # 当删除组标题时，级联删除所有子待办
    # foreign_keys 指定子待办的 group_id 字段
    # remote_side 指定父端（组标题）的 id 字段
    # single_parent=True 允许 delete-orphan cascade 在多对一关系的"多"端工作
    group_items = relationship(
        "Todo",
        foreign_keys=[group_id],
        remote_side=[id],
        backref="group_parent",
        cascade="all, delete-orphan",
        single_parent=True
    )


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    export_type = Column(String(16), nullable=False)  # csv, md7z
    status = Column(String(16), default="pending", nullable=False)  # pending, processing, completed, failed
    note_ids = Column(JSON, nullable=True)
    file_path = Column(String(512), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    report_path = Column(String(512), nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("User", backref="export_jobs")


class LoginAuditLog(Base):
    __tablename__ = "login_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    success = Column(Boolean, nullable=False)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    origin = Column(String(255), nullable=True)
    reason = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

