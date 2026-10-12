# -*- coding: utf-8 -*-
"""ORM 模型：待办（唯一核心表，见 CONTEXT.md）"""
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer

from app.database import Base


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(10), default="medium")   # high / medium / low
    tags = Column(Text, default="[]")                # JSON 数组字符串
    due_date = Column(DateTime, nullable=True)        # 到期时间（可空=只出现在"全部"视图）
    remind_at = Column(DateTime, nullable=True)       # 提醒触发时间（可空=不提醒）
    status = Column(String(10), default="pending")   # pending / completed
    completed_at = Column(DateTime, nullable=True)
    reminded = Column(Boolean, default=False)         # 提醒是否已触发（一次性保证）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
