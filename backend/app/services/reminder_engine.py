# -*- coding: utf-8 -*-
"""ReminderEngine — 深模块：提醒调度（任务单05填充行为）。

桩阶段仅提供会话工厂接缝，保证 conftest 注入可用。
"""
from app.database import SessionLocal


class ReminderEngine:
    """提醒引擎：扫描到期提醒 → 通知 → 标记（任务05实现）"""

    _session_factory = SessionLocal

    @classmethod
    def set_session_factory(cls, factory):
        """测试接缝：替换会话工厂"""
        cls._session_factory = factory

    def __init__(self, service, notifier, now):
        self.service = service
        self.notifier = notifier
        self.now = now

    def scan_and_fire(self) -> int:
        raise NotImplementedError("任务05实现")

    def backfill_missed(self) -> int:
        raise NotImplementedError("任务05实现")
