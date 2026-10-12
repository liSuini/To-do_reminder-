# -*- coding: utf-8 -*-
"""todo_service — 深模块：待办全部业务规则。

接缝：模块级函数 + set_session_factory（测试注入内存库）。
进出均为 dict，不暴露 ORM 对象。
"""
import json
from datetime import datetime

from app.database import SessionLocal
from app.models import Todo

_session_factory = SessionLocal


def set_session_factory(factory):
    """测试接缝：替换会话工厂"""
    global _session_factory
    _session_factory = factory


def _to_dict(todo: Todo) -> dict:
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description or "",
        "priority": todo.priority,
        "tags": json.loads(todo.tags or "[]"),
        "due_date": todo.due_date,
        "remind_at": todo.remind_at,
        "status": todo.status,
        "completed_at": todo.completed_at,
        "created_at": todo.created_at,
        "updated_at": todo.updated_at,
        "reminded": todo.reminded,
    }


def create_todo(data: dict) -> dict:
    session = _session_factory()
    try:
        todo = Todo(
            title=data["title"],
            description=data.get("description", "") or "",
            priority=data.get("priority", "medium"),
            tags=json.dumps(data.get("tags", []) or [], ensure_ascii=False),
            due_date=data.get("due_date"),
            remind_at=data.get("remind_at"),
        )
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return _to_dict(todo)
    finally:
        session.close()


def update_todo(todo_id: int, data: dict) -> dict | None:
    session = _session_factory()
    try:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return None
        if "title" in data and data["title"] is not None:
            todo.title = data["title"]
        if "description" in data and data["description"] is not None:
            todo.description = data["description"]
        if "priority" in data and data["priority"] is not None:
            todo.priority = data["priority"]
        if "tags" in data and data["tags"] is not None:
            todo.tags = json.dumps(data["tags"], ensure_ascii=False)
        if "due_date" in data:
            todo.due_date = data["due_date"]
        if "remind_at" in data:
            todo.remind_at = data["remind_at"]
            todo.reminded = False  # 修改提醒时间允许重新提醒
        session.commit()
        session.refresh(todo)
        return _to_dict(todo)
    finally:
        session.close()


def delete_todo(todo_id: int) -> bool:
    session = _session_factory()
    try:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return False
        session.delete(todo)
        session.commit()
        return True
    finally:
        session.close()


def set_completed(todo_id: int, completed: bool) -> dict | None:
    session = _session_factory()
    try:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return None
        todo.status = "completed" if completed else "pending"
        todo.completed_at = datetime.now() if completed else None
        session.commit()
        session.refresh(todo)
        return _to_dict(todo)
    finally:
        session.close()
