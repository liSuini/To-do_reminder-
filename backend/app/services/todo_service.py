# -*- coding: utf-8 -*-
"""todo_service — 深模块：待办全部业务规则。

接缝：模块级函数 + set_session_factory（测试注入内存库）。
进出均为 dict，不暴露 ORM 对象。

视图边界规则（CONTEXT.md）：
- today：due_date 在今日 00:00–24:00 之间
- week：due_date 在本周（周一至周日）内
- overdue：due_date < 今日 00:00 且 status=pending（已完成永不逾期）
- all：全部（无 due_date 的待办只出现在这里）
排序：priority 降序 → due_date 升序 → 无 due_date 排最后
"""
import json
from datetime import date, datetime, time, timedelta

from sqlalchemy import text

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


# ---------- 视图 / 筛选 / 排序 / 统计 ----------

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _day_start(d: date) -> datetime:
    return datetime.combine(d, time.min)


def _build_filters(view: str, tag: str | None, priority: str | None,
                   status: str | None, today: date):
    filters = []
    if view == "today":
        start = _day_start(today)
        filters.append(Todo.due_date >= start)
        filters.append(Todo.due_date < start + timedelta(days=1))
    elif view == "week":
        start = _day_start(today - timedelta(days=today.weekday()))  # 周一
        filters.append(Todo.due_date >= start)
        filters.append(Todo.due_date < start + timedelta(days=7))
    elif view == "overdue":
        filters.append(Todo.due_date < _day_start(today))
        filters.append(Todo.status == "pending")
    # view == "all"：不加条件
    if tag:
        # SQLite JSON1：标签存在 JSON 数组中（ADR-0002）
        filters.append(text(
            "EXISTS (SELECT 1 FROM json_each(todos.tags) WHERE json_each.value = :_tag)"
        ).bindparams(_tag=tag))
    if priority:
        filters.append(Todo.priority == priority)
    if status:
        filters.append(Todo.status == status)
    return filters


def query_todos(view: str = "all", tag: str | None = None,
                priority: str | None = None, status: str | None = None) -> list[dict]:
    session = _session_factory()
    try:
        q = session.query(Todo)
        for f in _build_filters(view, tag, priority, status, date.today()):
            q = q.filter(f)
        todos = q.all()
        todos.sort(key=lambda t: (
            _PRIORITY_ORDER.get(t.priority, 9),  # 优先级降序
            t.due_date is None,                  # 无日期最后
            t.due_date or datetime.max,          # 到期升序
        ))
        return [_to_dict(t) for t in todos]
    finally:
        session.close()


def get_stats(view: str = "all") -> dict:
    todos = query_todos(view=view)
    today_start = _day_start(date.today())
    overdue = sum(
        1 for t in todos
        if t["due_date"] and t["due_date"] < today_start and t["status"] == "pending"
    )
    return {
        "total": len(todos),
        "completed": sum(1 for t in todos if t["status"] == "completed"),
        "overdue": overdue,
    }


def get_tag_names() -> list[str]:
    """标签列表从现有待办动态派生（ADR-0002），不独立管理"""
    session = _session_factory()
    try:
        names: set[str] = set()
        for (tags_json,) in session.query(Todo.tags).all():
            for tag in json.loads(tags_json or "[]"):
                names.add(tag)
        return sorted(names)
    finally:
        session.close()
