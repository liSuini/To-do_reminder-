# -*- coding: utf-8 -*-
"""todo_service CRUD 行为规格"""
from app.services import todo_service


def test_create_todo(session):
    todo = todo_service.create_todo({
        "title": "测试待办", "priority": "high",
        "tags": ["工作"], "due_date": None, "remind_at": None,
    })
    assert todo["id"] == 1
    assert todo["status"] == "pending"
    assert todo["tags"] == ["工作"]
    assert todo["completed_at"] is None


def test_create_todo_defaults(session):
    todo = todo_service.create_todo({"title": "最简待办"})
    assert todo["priority"] == "medium"
    assert todo["tags"] == []
    assert todo["description"] == ""


def test_update_todo(session):
    todo_service.create_todo({"title": "旧标题"})
    updated = todo_service.update_todo(1, {"title": "新标题"})
    assert updated["title"] == "新标题"


def test_update_missing_returns_none(session):
    assert todo_service.update_todo(999, {"title": "x"}) is None


def test_update_remind_at_resets_reminded(session):
    from datetime import datetime, timedelta
    todo = todo_service.create_todo({
        "title": "改提醒", "remind_at": datetime.now() - timedelta(hours=1),
    })
    assert todo["reminded"] is False


def test_delete_todo(session):
    todo_service.create_todo({"title": "删除我"})
    assert todo_service.delete_todo(1) is True
    assert todo_service.delete_todo(1) is False


def test_set_completed_toggle(session):
    todo_service.create_todo({"title": "完成我"})
    done = todo_service.set_completed(1, True)
    assert done["status"] == "completed"
    assert done["completed_at"] is not None
    undone = todo_service.set_completed(1, False)
    assert undone["status"] == "pending"
    assert undone["completed_at"] is None


def test_set_completed_missing_returns_none(session):
    assert todo_service.set_completed(999, True) is None
