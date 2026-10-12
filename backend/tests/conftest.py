# -*- coding: utf-8 -*-
"""共享测试夹具：内存 SQLite + 会话工厂注入"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # noqa: F401 注册模型
from app.services import todo_service
from app.services.reminder_engine import ReminderEngine


@pytest.fixture
def session():
    """内存库会话：每个测试独立、互不干扰"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    S = sessionmaker(bind=engine)
    todo_service.set_session_factory(S)
    ReminderEngine.set_session_factory(S)  # 提醒引擎同样接受注入
    s = S()
    yield s
    s.close()
