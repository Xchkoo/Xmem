import datetime as dt
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
    todos = relationship("Todo", back_populates="owner", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    body_md = Column(Text, nullable=False)  # Markdown 格式内容
    is_pinned = Column(Boolean, default=False, nullable=False)  # 是否置顶
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
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="ledgers")


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False, nullable=False)  # 是否置顶
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

