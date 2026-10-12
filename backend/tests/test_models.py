import sys
from pathlib import Path

# 保证从 backend/ 目录内也能跑，从项目根也能跑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime

import pytest

from app.config import DB_PATH
from app.database import init_db, SessionLocal
from app.models import Todo


@pytest.fixture(autouse=True)
def clean_db():
    """测试前后清理文件库；Windows 需先释放连接池才能删文件"""
    from app.database import engine
    if DB_PATH.exists():
        DB_PATH.unlink()
    yield
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_create_and_query_todo():
    init_db()
    session = SessionLocal()
    try:
        todo = Todo(
            title="写周报",
            priority="high",
            tags='["工作"]',
            due_date=datetime(2026, 10, 12, 18, 0),
            remind_at=datetime(2026, 10, 12, 17, 0),
        )
        session.add(todo)
        session.commit()
        got = session.query(Todo).filter_by(title="写周报").first()
        assert got is not None
        assert got.priority == "high"
        assert got.status == "pending"
        assert got.reminded is False
    finally:
        session.close()
