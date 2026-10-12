# -*- coding: utf-8 -*-
"""视图边界/筛选/排序/统计 规格测试（CONTEXT.md 规则的可执行化）"""
from datetime import datetime, timedelta

from app.services import todo_service


def _seed():
    """造一批覆盖各种边界的数据：
    今日高优先 / 今日中优先 / 昨日未完成 / 昨日已完成 / 下周 / 无日期 / 今日带标签
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    todo_service.create_todo({"title": "今日高", "priority": "high",
                              "due_date": today.replace(hour=10)})
    todo_service.create_todo({"title": "今日中", "priority": "medium",
                              "due_date": today.replace(hour=12)})
    todo_service.create_todo({"title": "昨日未完成", "priority": "low",
                              "due_date": today - timedelta(days=1)})
    todo_service.create_todo({"title": "前日已完成", "priority": "low",
                              "due_date": today - timedelta(days=2)})
    todo_service.set_completed(4, True)
    todo_service.create_todo({"title": "下周", "priority": "low",
                              "due_date": today + timedelta(days=8)})
    todo_service.create_todo({"title": "无日期", "priority": "low"})
    todo_service.create_todo({"title": "带标签", "priority": "low",
                              "tags": ["工作", "会议"],
                              "due_date": today.replace(hour=15)})


def test_view_today(session):
    _seed()
    titles = [t["title"] for t in todo_service.query_todos(view="today")]
    assert titles == ["今日高", "今日中", "带标签"]  # 优先级降序，无日期不在


def test_view_week_scope(session):
    _seed()
    titles = [t["title"] for t in todo_service.query_todos(view="week")]
    assert "今日高" in titles        # 今天永远在本周
    assert "下周" not in titles      # 今天+8 天永远出本周（周长7天）


def test_view_overdue_excludes_completed(session):
    _seed()
    titles = [t["title"] for t in todo_service.query_todos(view="overdue")]
    assert titles == ["昨日未完成"]  # 已完成永不逾期


def test_view_all_contains_no_due_date(session):
    _seed()
    titles = [t["title"] for t in todo_service.query_todos(view="all")]
    assert "无日期" in titles


def test_filter_by_tag(session):
    _seed()
    titles = [t["title"] for t in todo_service.query_todos(view="all", tag="工作")]
    assert titles == ["带标签"]


def test_filter_by_priority(session):
    _seed()
    titles = [t["title"] for t in todo_service.query_todos(view="all", priority="high")]
    assert titles == ["今日高"]


def test_sort_priority_then_due(session):
    _seed()
    titles = [t["title"] for t in todo_service.query_todos(view="all")]
    assert titles.index("今日高") < titles.index("今日中")  # high 在 medium 前


def test_stats(session):
    _seed()
    stats = todo_service.get_stats(view="all")
    assert stats["total"] == 7
    assert stats["completed"] == 1
    assert stats["overdue"] == 1


def test_stats_overdue_in_today_view(session):
    _seed()
    stats = todo_service.get_stats(view="today")
    assert stats["overdue"] == 0  # 今日视图内无逾期


def test_tag_names_derived(session):
    _seed()
    names = todo_service.get_tag_names()
    assert "工作" in names and "会议" in names
    assert names == sorted(names)
