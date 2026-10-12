# -*- coding: utf-8 -*-
"""提醒引擎规格测试：假时钟 + SpyNotifier，不弹真实通知、不依赖真实时间"""
from datetime import datetime, timedelta

from app.services import todo_service
from app.services.reminder_engine import ReminderEngine


class SpyNotifier:
    """测试适配器：记录通知调用"""

    def __init__(self):
        self.sent = []

    def send(self, title, body):
        self.sent.append((title, body))


def _mk_engine(now: datetime):
    spy = SpyNotifier()
    engine = ReminderEngine(
        service=todo_service, notifier=spy, now=lambda: now,
    )
    return engine, spy


def test_scan_fires_due_reminder(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "该提醒了",
        "due_date": now + timedelta(minutes=5),
        "remind_at": now - timedelta(minutes=1),  # 提醒时间已过
    })
    engine, spy = _mk_engine(now)
    fired = engine.scan_and_fire()
    assert fired == 1
    assert spy.sent[0][0] == "待办提醒"
    assert "该提醒了" in spy.sent[0][1]


def test_reminder_fires_exactly_once(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "一次性",
        "due_date": now,
        "remind_at": now - timedelta(hours=1),
    })
    engine, spy = _mk_engine(now)
    assert engine.scan_and_fire() == 1
    assert engine.scan_and_fire() == 0  # 已标记，不重复
    assert len(spy.sent) == 1


def test_future_reminder_not_fired(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "未来的",
        "due_date": now + timedelta(days=1),
        "remind_at": now + timedelta(hours=1),
    })
    engine, spy = _mk_engine(now)
    assert engine.scan_and_fire() == 0
    assert spy.sent == []


def test_no_remind_at_never_fires(session):
    now = datetime.now()
    todo_service.create_todo({"title": "不设提醒", "due_date": now})
    engine, spy = _mk_engine(now)
    assert engine.scan_and_fire() == 0


def test_completed_todo_not_fired(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "已完成",
        "due_date": now,
        "remind_at": now - timedelta(hours=1),
    })
    todo_service.set_completed(1, True)
    engine, spy = _mk_engine(now)
    assert engine.scan_and_fire() == 0


def test_backfill_missed_on_startup(session):
    """应用没运行时错过的提醒，下次启动补发一次"""
    now = datetime.now()
    todo_service.create_todo({
        "title": "错过的",
        "due_date": now,
        "remind_at": now - timedelta(days=1),  # 远早于"当前时间"
    })
    engine, spy = _mk_engine(now)
    assert engine.backfill_missed() == 1
    assert len(spy.sent) == 1
    # 补发后不再重复
    assert engine.backfill_missed() == 0


def test_notifier_failure_does_not_break_scan(session):
    """单条通知失败不中断批量扫描（逐条隔离）"""
    now = datetime.now()

    class FailingNotifier:
        def send(self, title, body):
            raise RuntimeError("winotify 挂了")

    todo_service.create_todo({
        "title": "失败的", "due_date": now, "remind_at": now - timedelta(hours=1),
    })
    todo_service.create_todo({
        "title": "正常的", "due_date": now, "remind_at": now - timedelta(hours=2),
    })
    spy = SpyNotifier()

    class MixedNotifier:
        """第一条失败，第二条成功"""
        def __init__(self):
            self.calls = 0
        def send(self, title, body):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("第一条挂了")
            spy.send(title, body)

    engine = ReminderEngine(service=todo_service, notifier=MixedNotifier(), now=lambda: now)
    fired = engine.scan_and_fire()
    assert fired == 1          # 第二条成功
    assert spy.sent[0][1].find("正常") >= 0
