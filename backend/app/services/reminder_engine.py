# -*- coding: utf-8 -*-
"""ReminderEngine — 深模块：提醒调度。

规则（CONTEXT.md）：
- 提醒是一次性事件：触发即标记 reminded，不重复弹出
- 错过补发：应用未运行期间到期的提醒，下次启动补发一次
- 已完成/无 remind_at 的待办不触发
- 单条通知失败不影响后续（逐条 try/except + 日志）

接缝：notifier（生产 winotify / 测试 Spy）与 now（时钟）均可注入。
"""
import logging

from app.database import SessionLocal
from app.models import Todo

logger = logging.getLogger(__name__)


class ReminderEngine:

    _session_factory = SessionLocal

    @classmethod
    def set_session_factory(cls, factory):
        """测试接缝：替换会话工厂"""
        cls._session_factory = factory

    def __init__(self, service, notifier, now):
        self.service = service
        self.notifier = notifier
        self.now = now

    def _fire(self, todo) -> bool:
        """弹一条通知；失败返回 False 且不标记"""
        try:
            body = f"「{todo.title}」"
            if todo.due_date:
                body += f" 截止：{todo.due_date:%m-%d %H:%M}"
            self.notifier.send("待办提醒", body)
            return True
        except Exception:
            logger.exception("通知发送失败 todo_id=%s", todo.id)
            return False

    def scan_and_fire(self) -> int:
        """扫描到期提醒 → 通知 → 标记，返回本次触发数"""
        now = self.now()
        session = self._session_factory()
        fired = 0
        try:
            rows = session.query(Todo).filter(
                Todo.remind_at.isnot(None),
                Todo.remind_at <= now,
                Todo.reminded.is_(False),
                Todo.status == "pending",
            ).all()
            for todo in rows:
                if self._fire(todo):
                    todo.reminded = True
                    fired += 1
            session.commit()
        finally:
            session.close()
        return fired

    def backfill_missed(self) -> int:
        """启动补发：与扫描同语义（错过即 remind_at 已过且未标记），一次性"""
        return self.scan_and_fire()
