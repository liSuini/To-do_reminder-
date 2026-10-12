# -*- coding: utf-8 -*-
"""Pydantic 请求/响应 Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    tags: list[str] = []
    due_date: Optional[datetime] = None
    remind_at: Optional[datetime] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern="^(high|medium|low)$")
    tags: Optional[list[str]] = None
    due_date: Optional[datetime] = None
    remind_at: Optional[datetime] = None


class TodoOut(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    tags: list[str]
    due_date: Optional[datetime]
    remind_at: Optional[datetime]
    status: str
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
