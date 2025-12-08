import datetime as dt
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    ledgers = relationship("LedgerEntry", back_populates="owner", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="owner", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    body = Column(Text, nullable=False)
    attachment_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    owner = relationship("User", back_populates="notes")


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
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="ledgers")


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="todos")

