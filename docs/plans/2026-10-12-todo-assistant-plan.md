# 待办助手（To-do Reminder）实现计划

> **执行说明**：本计划按任务逐个执行，每个任务走 TDD 循环（写失败测试→验证失败→最小实现→验证通过→提交）。步骤用复选框（`- [ ]`）跟踪。

**目标**：交付一个可双击运行的 Windows 桌面待办助手（新建待办/提醒/优先级/标签/多视图/系统通知）。

**架构**：Electron 主进程管理窗口与 Python 子进程；FastAPI 后端提供 API 并托管 Vue3 静态产物；APScheduler+winotify 负责提醒。详见架构设计文档。

**技术栈**：Python 3.14 + FastAPI + SQLAlchemy + SQLite + APScheduler + winotify + PyInstaller；Vue3 + Element Plus + Vite；Electron + electron-builder。

**规格依据**：`docs/specs/2026-10-12-architecture-design.md` + `tasks/prd-todo-assistant.md` + `CONTEXT.md`（领域规则）

## 全局约束

- Python 解释器固定 `D:\developTools\python\python3.14.5\python.exe`，所有 python 调用带 `-X utf8`（中文路径兼容）
- 依赖安装一律 `python -m pip`，不污染全局环境（backend venv 或 --target 隔离）
- Electron 二进制下载必须 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/`
- 领域规则以 `CONTEXT.md` 为准：无 due_date 的待办只在"全部"视图；已完成永不逾期；提醒一次性；错过启动补发一次
- 排序规则：priority 降序（high>medium>low），同级 due_date 升序，无 due_date 排最后
- 测试不弹真实 Windows 通知（SpyNotifier），不依赖真实时钟（注入 now）
- 提交信息格式：`feat:`/`test:`/`fix:`/`chore:` 前缀

---

### Task 1: 后端骨架与数据模型

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`（空）
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/schemas.py`
- Create: `backend/tests/test_models.py`
- Create: `backend/pytest.ini`

**Interfaces:**
- Produces: `Todo` ORM 模型（字段见表）、`SessionLocal`/`engine`、`init_db()`、Pydantic `TodoCreate/TodoUpdate/TodoOut`

- [ ] **Step 1: 安装依赖**

```
D:\developTools\python\python3.14.5\python.exe -m pip install fastapi uvicorn sqlalchemy pydantic apscheduler winotify pytest httpx --quiet
```

`backend/requirements.txt`：

```
fastapi
uvicorn
sqlalchemy
pydantic
apscheduler
winotify
```

- [ ] **Step 2: 写失败测试**

`backend/tests/test_models.py`：

```python
import sys
sys.path.insert(0, ".")

from datetime import datetime
from app.database import init_db, SessionLocal
from app.models import Todo


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
```

- [ ] **Step 3: 运行验证失败**

```
D:\developTools\python\python3.14.5\python.exe -X utf8 -m pytest backend/tests/test_models.py -v
```
预期：FAIL（No module named 'app'）

- [ ] **Step 4: 最小实现**

`backend/app/config.py`：

```python
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "todo.db"
DEFAULT_PORT = 8000
SCAN_INTERVAL_SECONDS = 30
PORT_FILE = Path(__file__).resolve().parent.parent / "backend.port"
```

`backend/app/database.py`：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DB_PATH

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def init_db():
    from app import models  # noqa: F401 确保模型注册
    Base.metadata.create_all(engine)
```

`backend/app/models.py`：

```python
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, Integer
from app.database import Base


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(10), default="medium")  # high/medium/low
    tags = Column(Text, default="[]")                 # JSON 数组字符串
    due_date = Column(DateTime, nullable=True)
    remind_at = Column(DateTime, nullable=True)
    status = Column(String(10), default="pending")    # pending/completed
    completed_at = Column(DateTime, nullable=True)
    reminded = Column(Boolean, default=False)         # 提醒是否已触发
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

`backend/app/schemas.py`：

```python
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
```

注意：`Column` 需从 `sqlalchemy` 导入，实现时补 `from sqlalchemy import Column`。

`backend/pytest.ini`：

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 5: 运行验证通过**

```
D:\developTools\python\python3.14.5\python.exe -X utf8 -m pytest backend/tests/ -v
```
预期：PASS；删除测试产生的 todo.db（测试后清理，见 Task 4 用内存库替代）

- [ ] **Step 6: Commit**

```
git add backend/
git commit -m "feat: 后端骨架与数据模型"
```

---

### Task 2: todo_service — CRUD

**Files:**
- Create: `backend/app/services/__init__.py`（空）
- Create: `backend/app/services/todo_service.py`
- Test: `backend/tests/test_todo_service.py`

**Interfaces:**
- Consumes: `Todo` 模型、`SessionLocal`、`init_db`
- Produces: `create_todo(data: dict) -> dict`、`update_todo(todo_id, data: dict) -> dict|None`、`delete_todo(todo_id) -> bool`、`set_completed(todo_id, completed: bool) -> dict|None`（返回 TodoOut 形状 dict；测试需支持注入 session 工厂以便用内存库）

- [ ] **Step 1: 写失败测试**

`backend/tests/test_todo_service.py`（用 SQLite 内存库隔离）：

```python
import sys
sys.path.insert(0, ".")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # noqa
from app.services import todo_service


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    S = sessionmaker(bind=engine)
    todo_service.set_session_factory(S)  # 接缝：测试注入内存会话工厂
    s = S()
    yield s
    s.close()


def test_create_todo(session):
    todo = todo_service.create_todo({
        "title": "测试待办", "priority": "high",
        "tags": ["工作"], "due_date": None, "remind_at": None,
    })
    assert todo["id"] == 1
    assert todo["status"] == "pending"
    assert todo["tags"] == ["工作"]


def test_update_todo(session):
    todo_service.create_todo({"title": "旧标题"})
    updated = todo_service.update_todo(1, {"title": "新标题"})
    assert updated["title"] == "新标题"


def test_update_missing_returns_none(session):
    assert todo_service.update_todo(999, {"title": "x"}) is None


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
```

- [ ] **Step 2: 运行验证失败**

预期：FAIL（todo_service 不存在）

- [ ] **Step 3: 最小实现**

`backend/app/services/todo_service.py`：

```python
"""深模块：全部待办业务规则。进出均为 dict，不暴露 ORM。"""
import json
from datetime import datetime
from app.database import SessionLocal
from app.models import Todo


_session_factory = SessionLocal


def set_session_factory(factory):
    """测试接缝：替换会话工厂（内存库）"""
    global _session_factory
    _session_factory = factory


def _to_dict(todo: Todo) -> dict:
    return {
        "id": todo.id, "title": todo.title, "description": todo.description,
        "priority": todo.priority, "tags": json.loads(todo.tags or "[]"),
        "due_date": todo.due_date, "remind_at": todo.remind_at,
        "status": todo.status, "completed_at": todo.completed_at,
        "created_at": todo.created_at, "updated_at": todo.updated_at,
        "reminded": todo.reminded,
    }


def create_todo(data: dict) -> dict:
    session = _session_factory()
    try:
        todo = Todo(
            title=data["title"],
            description=data.get("description", ""),
            priority=data.get("priority", "medium"),
            tags=json.dumps(data.get("tags", []), ensure_ascii=False),
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
            todo.reminded = False  # 改提醒时间则允许重新提醒
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
```

- [ ] **Step 4: 运行验证通过**

- [ ] **Step 5: Commit** `feat: todo_service CRUD`

---

### Task 3: todo_service — 视图/筛选/排序/统计

**Files:**
- Modify: `backend/app/services/todo_service.py`
- Test: `backend/tests/test_views.py`

**Interfaces:**
- Produces: `query_todos(view="all", tag=None, priority=None, status=None) -> list[dict]`、`get_stats(view="all") -> dict`、`get_tag_names() -> list[str]`
- 视图规则（CONTEXT.md）：today=今日00:00–23:59；week=本周一至周日；overdue=due<今日0点 且 status=pending；all=全部

- [ ] **Step 1: 写失败测试**

`backend/tests/test_views.py`：

```python
import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta
from app.services import todo_service


def _seed(session):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    todo_service.create_todo({"title": "今日高", "priority": "high",
                              "due_date": today.replace(hour=10)})
    todo_service.create_todo({"title": "今日中", "priority": "medium",
                              "due_date": today.replace(hour=12)})
    todo_service.create_todo({"title": "昨日未完成", "priority": "low",
                              "due_date": today - timedelta(days=1)})
    todo_service.create_todo({"title": "昨日已完成", "priority": "low",
                              "due_date": today - timedelta(days=2)})
    todo_service.set_completed(4, True)
    todo_service.create_todo({"title": "下周", "priority": "low",
                              "due_date": today + timedelta(days=8)})
    todo_service.create_todo({"title": "无日期", "priority": "low"})
    todo_service.create_todo({"title": "带标签", "priority": "low",
                              "tags": ["工作", "会议"],
                              "due_date": today.replace(hour=15)})


def test_view_today(session):
    _seed(session)
    titles = [t["title"] for t in todo_service.query_todos(view="today")]
    assert titles == ["今日高", "今日中", "带标签"]  # 优先级降序


def test_view_week(session):
    _seed(session)
    titles = [t["title"] for t in todo_service.query_todos(view="week")]
    assert "下周" not in titles
    assert "昨日未完成" in titles  # 只要在本周（周一起），不管是否逾期


def test_view_overdue(session):
    _seed(session)
    titles = [t["title"] for t in todo_service.query_todos(view="overdue")]
    assert titles == ["昨日未完成"]  # 已完成不算逾期；昨天的"昨日已完成"排除


def test_view_all_excludes_no_due_date_from_others(session):
    _seed(session)
    titles = [t["title"] for t in todo_service.query_todos(view="today")]
    assert "无日期" not in titles
    all_titles = [t["title"] for t in todo_service.query_todos(view="all")]
    assert "无日期" in all_titles


def test_filter_by_tag(session):
    _seed(session)
    titles = [t["title"] for t in todo_service.query_todos(view="all", tag="工作")]
    assert titles == ["带标签"]


def test_stats(session):
    _seed(session)
    stats = todo_service.get_stats(view="all")
    assert stats["total"] == 7
    assert stats["completed"] == 1
    assert stats["overdue"] == 1


def test_tag_names(session):
    _seed(session)
    names = todo_service.get_tag_names()
    assert "工作" in names and "会议" in names
```

- [ ] **Step 2: 运行验证失败**

- [ ] **Step 3: 最小实现**（追加到 todo_service.py）

```python
from datetime import date, timedelta
from sqlalchemy import func, and_


def _week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def _build_filters(view: str, tag, priority, status, today: date):
    filters = []
    if view == "today":
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)
        filters.append(Todo.due_date >= start)
        filters.append(Todo.due_date < end)
    elif view == "week":
        start = datetime.combine(_week_start(today), datetime.min.time())
        end = start + timedelta(days=7)
        filters.append(Todo.due_date >= start)
        filters.append(Todo.due_date < end)
    elif view == "overdue":
        filters.append(Todo.due_date < datetime.combine(today, datetime.min.time()))
        filters.append(Todo.status == "pending")
    if tag:
        filters.append(func.exists(
            func.json_each(Todo.tags).table_valued("value")  # SQLite json_each
        ))  # 注：实现时改用 SQLite JSON1 原生查询 text("EXISTS (SELECT 1 FROM json_each(todos.tags) WHERE value=:tag)") 并绑定参数
    if priority:
        filters.append(Todo.priority == priority)
    if status:
        filters.append(Todo.status == status)
    return filters


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def query_todos(view="all", tag=None, priority=None, status=None) -> list[dict]:
    session = _session_factory()
    try:
        q = session.query(Todo)
        for f in _build_filters(view, tag, priority, status, date.today()):
            q = q.filter(f)
        todos = q.all()
        todos.sort(key=lambda t: (
            _PRIORITY_ORDER.get(t.priority, 9),
            t.due_date is None,          # 无日期排最后
            t.due_date or datetime.max,
        ))
        return [_to_dict(t) for t in todos]
    finally:
        session.close()


def get_stats(view="all") -> dict:
    all_todos = query_todos(view=view)
    today = date.today()
    overdue = sum(
        1 for t in all_todos
        if t["due_date"] and t["due_date"] < datetime.combine(today, datetime.min.time())
        and t["status"] == "pending"
    )
    return {
        "total": len(all_todos),
        "completed": sum(1 for t in all_todos if t["status"] == "completed"),
        "overdue": overdue,
    }


def get_tag_names() -> list[str]:
    session = _session_factory()
    try:
        names = set()
        for (tags_json,) in session.query(Todo.tags):
            for tag in json.loads(tags_json or "[]"):
                names.add(tag)
        return sorted(names)
    finally:
        session.close()
```

注意：标签筛选的 json_each 在实现时用原生 SQL 文本方式（`from sqlalchemy import text`），上面 func 写法仅为示意，以测试通过为准。

- [ ] **Step 4: 运行验证通过**

- [ ] **Step 5: Commit** `feat: 视图/筛选/排序/统计`

---

### Task 4: API 路由层

**Files:**
- Create: `backend/app/routers/__init__.py`（空）
- Create: `backend/app/routers/todos.py`
- Create: `backend/app/routers/system.py`
- Create: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: todo_service 全部函数
- Produces: HTTP 端点（POST/GET/PUT/DELETE /api/todos、PATCH /api/todos/{id}/complete、GET /api/health）

- [ ] **Step 1: 写失败测试**

`backend/tests/test_api.py`：

```python
import sys
sys.path.insert(0, ".")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # noqa
from app.routers import make_app  # 组装函数（Task 6 前的过渡版）


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    S = sessionmaker(bind=engine)
    from app.services import todo_service
    todo_service.set_session_factory(S)
    app = make_app()
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_and_get(client):
    r = client.post("/api/todos", json={"title": "API测试", "priority": "high"})
    assert r.status_code == 200
    todo_id = r.json()["id"]
    r2 = client.get(f"/api/todos/{todo_id}")
    assert r2.json()["title"] == "API测试"


def test_create_validation_error(client):
    r = client.post("/api/todos", json={"title": ""})
    assert r.status_code == 422


def test_view_query(client):
    client.post("/api/todos", json={"title": "a"})
    r = client.get("/api/todos", params={"view": "today"})
    assert r.status_code == 200
    assert r.json() == []  # 无 due_date 不在今日视图


def test_complete_toggle(client):
    todo_id = client.post("/api/todos", json={"title": "完成"}).json()["id"]
    r = client.patch(f"/api/todos/{todo_id}/complete", json={"completed": True})
    assert r.json()["status"] == "completed"


def test_tags_endpoint(client):
    client.post("/api/todos", json={"title": "t", "tags": ["工作"]})
    assert "工作" in client.get("/api/tags").json()


def test_stats_endpoint(client):
    r = client.get("/api/stats", params={"view": "all"})
    assert r.json() == {"total": 0, "completed": 0, "overdue": 0}


def test_delete_and_404(client):
    todo_id = client.post("/api/todos", json={"title": "x"}).json()["id"]
    assert client.delete(f"/api/todos/{todo_id}").status_code == 200
    assert client.get(f"/api/todos/{todo_id}").status_code == 404
```

- [ ] **Step 2: 运行验证失败**

- [ ] **Step 3: 最小实现**

`backend/app/routers/todos.py`：

```python
from fastapi import APIRouter, HTTPException
from app.schemas import TodoCreate, TodoUpdate
from app.services import todo_service

router = APIRouter(prefix="/api")


@router.post("/todos")
def create_todo(payload: TodoCreate):
    return todo_service.create_todo(payload.model_dump())


@router.get("/todos")
def list_todos(view: str = "all", tag: str | None = None,
               priority: str | None = None, status: str | None = None):
    return todo_service.query_todos(view=view, tag=tag, priority=priority, status=status)


@router.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    todos = todo_service.query_todos(view="all")
    for t in todos:
        if t["id"] == todo_id:
            return t
    raise HTTPException(404)


@router.put("/todos/{todo_id}")
def update_todo(todo_id: int, payload: TodoUpdate):
    result = todo_service.update_todo(todo_id, payload.model_dump(exclude_none=False))
    if result is None:
        raise HTTPException(404)
    return result


@router.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    if not todo_service.delete_todo(todo_id):
        raise HTTPException(404)
    return {"ok": True}


@router.patch("/todos/{todo_id}/complete")
def complete_todo(todo_id: int, body: dict):
    result = todo_service.set_completed(todo_id, bool(body.get("completed", True)))
    if result is None:
        raise HTTPException(404)
    return result


@router.get("/tags")
def tags():
    return todo_service.get_tag_names()


@router.get("/stats")
def stats(view: str = "all"):
    return todo_service.get_stats(view=view)
```

注：`get_todo` 先用全量过滤，实现时可在 todo_service 加 `get_todo(todo_id)` 直查（性能与简洁都更好，允许实现者补充并配测试）。

`backend/app/routers/system.py`：

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}
```

`backend/app/routers/__init__.py`：

```python
from fastapi import FastAPI
from app.routers.todos import router as todos_router
from app.routers.system import router as system_router


def make_app() -> FastAPI:
    app = FastAPI(title="待办助手")
    app.include_router(todos_router)
    app.include_router(system_router)
    return app
```

- [ ] **Step 4: 运行验证通过**

- [ ] **Step 5: Commit** `feat: API 路由层`

---

### Task 5: 提醒引擎 reminder_engine

**Files:**
- Create: `backend/app/services/reminder_engine.py`
- Create: `backend/app/notify/__init__.py`（空）
- Create: `backend/app/notify/winotify_notifier.py`
- Test: `backend/tests/test_reminder_engine.py`

**Interfaces:**
- Consumes: `Notifier` 协议（send(title, body)）、todo_service
- Produces: `ReminderEngine(service=todo_service, notifier, now)`、`scan_and_fire() -> int`、`backfill_missed() -> int`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_reminder_engine.py`：

```python
import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta
from app.services import todo_service
from app.services.reminder_engine import ReminderEngine


class SpyNotifier:
    def __init__(self):
        self.sent = []

    def send(self, title, body):
        self.sent.append((title, body))


def _mk_engine(now):
    spy = SpyNotifier()
    return ReminderEngine(service=todo_service, notifier=spy, now=lambda: now), spy


def test_scan_fires_due_reminder(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "该提醒了", "due_date": now + timedelta(minutes=5),
        "remind_at": now - timedelta(minutes=1),
    })
    engine, spy = _mk_engine(now)
    fired = engine.scan_and_fire()
    assert fired == 1
    assert spy.sent[0][0] == "待办提醒"
    assert "该提醒了" in spy.sent[0][1]


def test_reminder_fires_once(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "一次性", "due_date": now, "remind_at": now - timedelta(hours=1),
    })
    engine, spy = _mk_engine(now)
    assert engine.scan_and_fire() == 1
    assert engine.scan_and_fire() == 0  # 不重复
    assert len(spy.sent) == 1


def test_future_reminder_not_fired(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "未来的", "due_date": now + timedelta(days=1),
        "remind_at": now + timedelta(hours=1),
    })
    engine, spy = _mk_engine(now)
    assert engine.scan_and_fire() == 0
    assert spy.sent == []


def test_completed_todo_not_fired(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "已完成", "due_date": now, "remind_at": now - timedelta(hours=1),
    })
    todo_service.set_completed(1, True)
    engine, spy = _mk_engine(now)
    assert engine.scan_and_fire() == 0


def test_backfill_missed(session):
    now = datetime.now()
    todo_service.create_todo({
        "title": "错过的", "due_date": now,
        "remind_at": now - timedelta(days=1),
    })
    engine, spy = _mk_engine(now)
    assert engine.backfill_missed() == 1
    assert len(spy.sent) == 1
```

- [ ] **Step 2: 运行验证失败**

- [ ] **Step 3: 最小实现**

`backend/app/notify/winotify_notifier.py`：

```python
from winotify import Notification, audio


class WinotifyNotifier:
    """生产适配器：Windows 原生 Toast"""
    def send(self, title: str, body: str):
        toast = Notification(app_id="待办助手", title=title, msg=body, duration="short")
        toast.set_audio(audio.Default, loop=False)
        toast.show()
```

`backend/app/services/reminder_engine.py`：

```python
"""深模块：提醒调度。注入 notifier 与 now，测试不弹真实通知。"""
import logging
from datetime import datetime
from app.database import SessionLocal
from app.models import Todo

logger = logging.getLogger(__name__)


class ReminderEngine:
    def __init__(self, service, notifier, now):
        self.service = service
        self.notifier = notifier
        self.now = now

    def _due_reminders(self, now):
        session = SessionLocal()
        try:
            if hasattr(self.service, "_session_factory"):
                # 测试注入过的工厂同样作用于直查——见实现说明
                pass
            rows = session.query(Todo).filter(
                Todo.remind_at.isnot(None),
                Todo.remind_at <= now,
                Todo.reminded.is_(False),
                Todo.status == "pending",
            ).order_by(Todo.remind_at.desc()).all()
            return rows
        finally:
            session.close()

    def _fire(self, todo) -> bool:
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
        now = self.now()
        session = SessionLocal()
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
        return self.scan_and_fire()
```

实现说明：引擎直查 ORM 而非走 service（避免浅包装），但测试需要内存库——因此引擎也提供 `set_session_factory` 同款接缝（与 todo_service 相同模式），测试 fixture 中同时注入。补发与扫描同一查询语义（CONTEXT.md：错过补发只补一次），backfill_missed 即 scan_and_fire，语义上分开命名是为了将来区分（当前 YAGNI 合并实现，保留两个入口名）。

- [ ] **Step 4: 运行验证通过**

- [ ] **Step 5: Commit** `feat: 提醒引擎（调度/一次性/补发）`

---

### Task 6: runner 组装根 + 开发启动入口

**Files:**
- Create: `backend/app/runner.py`
- Create: `backend/start_dev.py`
- Test: `backend/tests/test_runner.py`

**Interfaces:**
- Consumes: make_app、init_db、ReminderEngine、WinotifyNotifier
- Produces: `create_app()`（含静态托管/调度启动/补发）、`find_free_port(start)`、端口写入 `backend.port`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_runner.py`：

```python
import sys
sys.path.insert(0, ".")

import socket


def test_find_free_port_returns_usable():
    from app.runner import find_free_port
    port = find_free_port(8000)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))  # 能绑定说明确实可用


def test_create_app_has_health():
    from app.runner import create_app
    from fastapi.testclient import TestClient
    client = TestClient(create_app())
    assert client.get("/api/health").status_code == 200
```

- [ ] **Step 2: 运行验证失败** → **Step 3: 实现**

`backend/app/runner.py`：

```python
"""组装根：唯一知道一切如何拼起来的地方。"""
import socket
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import DEFAULT_PORT, PORT_FILE, SCAN_INTERVAL_SECONDS
from app.database import init_db
from app.notify.winotify_notifier import WinotifyNotifier
from app.routers import make_app
from app.services.reminder_engine import ReminderEngine


def find_free_port(start: int = DEFAULT_PORT) -> int:
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("无可用端口")


def create_app(start_scheduler: bool = True) -> FastAPI:
    init_db()
    app = make_app()

    engine = ReminderEngine(
        service=None, notifier=WinotifyNotifier(),
        now=__import__("datetime").datetime.now,
    )
    engine.backfill_missed()  # 启动补发（CONTEXT.md 规则）

    if start_scheduler:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            engine.scan_and_fire, "interval",
            seconds=SCAN_INTERVAL_SECONDS, max_instances=1,
        )
        scheduler.start()
        app.state.scheduler = scheduler

    dist = Path(__file__).resolve().parent.parent / "frontend_dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="static")
    return app


def main():
    import uvicorn
    port = find_free_port(DEFAULT_PORT)
    PORT_FILE.write_text(str(port), encoding="utf-8")
    print(f"BACKEND_READY port={port}", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
```

`backend/start_dev.py`：

```python
"""开发模式入口：python -X utf8 start_dev.py"""
from app.runner import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行验证通过**（TestClient 环境下 start_scheduler=False 路径也要覆盖）
- [ ] **Step 5: Commit** `feat: runner 组装根与端口探测`

---

### Task 7: 前端骨架（Vite + Vue3 + Element Plus）

**Files:**
- Create: `frontend/`（vite 脚手架）、`frontend/src/api.js`、`frontend/src/composables/useTodos.js`、`frontend/src/App.vue`、`frontend/src/main.js`
- Consumes: 后端 API（Task 4）

- [ ] **Step 1: 初始化脚手架**

```
cd frontend
npm create vite@latest . -- --template vue
npm install element-plus
npm install
```

- [ ] **Step 2: api.js**

```javascript
// frontend/src/api.js
const BASE = "";  // 同源（开发模式走 vite proxy）

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

export const api = {
  listTodos: (params) => request(`/api/todos?${new URLSearchParams(params)}`),
  createTodo: (data) => request("/api/todos", { method: "POST", body: JSON.stringify(data) }),
  updateTodo: (id, data) => request(`/api/todos/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteTodo: (id) => request(`/api/todos/${id}`, { method: "DELETE" }),
  completeTodo: (id, completed) => request(`/api/todos/${id}/complete`, { method: "PATCH", body: JSON.stringify({ completed }) }),
  getTags: () => request("/api/tags"),
  getStats: (view) => request(`/api/stats?view=${view}`),
};
```

- [ ] **Step 3: useTodos.js（前端唯一状态源）**

```javascript
import { ref, reactive } from "vue";
import { api } from "../api";

export function useTodos() {
  const currentView = ref("today");
  const currentTag = ref(null);
  const todos = ref([]);
  const tags = ref([]);
  const stats = reactive({ total: 0, completed: 0, overdue: 0 });
  const loading = ref(false);

  async function refresh() {
    loading.value = true;
    try {
      const params = { view: currentView.value };
      if (currentTag.value) params.tag = currentTag.value;
      todos.value = await api.listTodos(params);
      Object.assign(stats, await api.getStats(currentView.value));
      tags.value = await api.getTags();
    } finally {
      loading.value = false;
    }
  }

  function switchView(view) { currentView.value = view; currentTag.value = null; return refresh(); }
  function switchTag(tag) { currentTag.value = tag; return refresh(); }
  function clearTag() { currentTag.value = null; return refresh(); }

  return { currentView, currentTag, todos, tags, stats, loading, refresh,
           switchView, switchTag, clearTag };
}
```

- [ ] **Step 4: App.vue 三区布局**

```vue
<template>
  <el-container class="app">
    <el-aside width="200px"><Sidebar /></el-aside>
    <el-container>
      <el-main><TodoList /></el-main>
      <el-footer height="32px"><StatusBar /></el-footer>
    </el-container>
  </el-container>
</template>
<script setup>
import Sidebar from "./components/Sidebar.vue";
import TodoList from "./components/TodoList.vue";
import StatusBar from "./components/StatusBar.vue";
</script>
<style>
html, body, #app, .app { height: 100%; margin: 0; }
</style>
```

`main.js` 挂 ElementPlus；`vite.config.js` 加 `server.proxy`：`"/api" → "http://127.0.0.1:8000"`。

- [ ] **Step 5: 验证** `npm run dev` 页面三区完整（组件空实现先占位）
- [ ] **Step 6: Commit** `feat: 前端骨架`

---

### Task 8: 待办列表与视图切换

**Files:**
- Create: `frontend/src/components/Sidebar.vue`、`TodoList.vue`、`TodoCard.vue`
- Consumes: useTodos（Task 7）

- [ ] **Step 1: Sidebar.vue**（视图四入口 + 标签列表）

```vue
<template>
  <el-menu :default-active="currentView" @select="onView">
    <el-menu-item index="today">今日</el-menu-item>
    <el-menu-item index="week">本周</el-menu-item>
    <el-menu-item index="overdue">已逾期</el-menu-item>
    <el-menu-item index="all">全部</el-menu-item>
  </el-menu>
  <el-divider>标签</el-divider>
  <el-tag v-for="t in tags" :key="t" :effect="currentTag===t ? 'dark' : 'plain'"
          style="margin: 4px; cursor: pointer" @click="onTag(t)">{{ t }}</el-tag>
  <el-button v-if="currentTag" link @click="clearTag()">清除筛选</el-button>
</template>
<script setup>
import { useTodos } from "../composables/useTodos";
const { currentView, currentTag, tags, switchView, switchTag, clearTag } = useTodos();
const onView = (v) => switchView(v);
const onTag = (t) => switchTag(t);
</script>
```

注意：useTodos 需改为模块级单例（`const state = ...` 移到函数外），供多组件共享同一状态；Task 7 实现时直接按单例写。

- [ ] **Step 2: TodoCard.vue**（优先级色块/标签/到期时间/操作）

```vue
<template>
  <el-card :class="['todo-card', todo.priority, todo.status]" shadow="hover">
    <el-checkbox :model-value="todo.status === 'completed'"
                 @change="onComplete" />
    <span class="dot" :class="todo.priority" />
    <span class="title">{{ todo.title }}</span>
    <el-tag v-for="t in todo.tags" :key="t" size="small" type="info">{{ t }}</el-tag>
    <span v-if="todo.due_date" class="due">🕐 {{ fmt(todo.due_date) }}</span>
    <el-button link @click="$emit('edit', todo)">编辑</el-button>
    <el-popconfirm title="删除该待办？" @confirm="onDelete">
      <template #reference><el-button link type="danger">删除</el-button></template>
    </el-popconfirm>
  </el-card>
</template>
<script setup>
import { useTodos } from "../composables/useTodos";
const props = defineProps({ todo: Object });
defineEmits(["edit"]);
const { completeTodo, deleteTodo, refresh } = useTodos();
const onComplete = (v) => completeTodo(props.todo.id, v).then(refresh);
const onDelete = () => deleteTodo(props.todo.id).then(refresh);
const fmt = (d) => new Date(d).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
</script>
<style scoped>
.todo-card.completed .title { text-decoration: line-through; color: #999; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.dot.high { background: #f56c6c; } .dot.medium { background: #e6a23c; } .dot.low { background: #909399; }
</style>
```

- [ ] **Step 3: TodoList.vue**（列表 + 新建按钮 + 空状态）

```vue
<template>
  <div>
    <el-button type="primary" @click="dialog = true">+ 新建待办</el-button>
    <TodoForm v-model="dialog" :todo="editing" @saved="refresh" />
    <el-empty v-if="!loading && !todos.length" description="暂无待办" />
    <TodoCard v-for="t in todos" :key="t.id" :todo="t" @edit="onEdit" />
  </div>
</template>
<script setup>
import { ref } from "vue";
import { useTodos } from "../composables/useTodos";
import TodoCard from "./TodoCard.vue";
import TodoForm from "./TodoForm.vue";
const { todos, loading, refresh } = useTodos();
const dialog = ref(false);
const editing = ref(null);
const onEdit = (todo) => { editing.value = todo; dialog.value = true; };
refresh();
</script>
```

- [ ] **Step 4: 浏览器验证**：启动后端 + `npm run dev`，验证视图切换、标签筛选、排序、空状态（对应 US-002/US-003）
- [ ] **Step 5: Commit** `feat: 待办列表与视图切换`

---

### Task 9: 新建/编辑表单 TodoForm

**Files:**
- Create: `frontend/src/components/TodoForm.vue`
- Consumes: api.createTodo / updateTodo

- [ ] **Step 1: 实现**

```vue
<template>
  <el-dialog :model-value="modelValue" :title="todo ? '编辑待办' : '新建待办'"
             @update:model-value="$emit('update:modelValue', $event)" width="480px">
    <el-form :model="form" label-width="80px">
      <el-form-item label="标题" required>
        <el-input v-model="form.title" placeholder="要做什么？" maxlength="200" />
      </el-form-item>
      <el-form-item label="详细内容">
        <el-input v-model="form.description" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="优先级">
        <el-radio-group v-model="form.priority">
          <el-radio value="high">高</el-radio>
          <el-radio value="medium">中</el-radio>
          <el-radio value="low">低</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="标签">
        <el-select v-model="form.tags" multiple allow-create filterable
                   placeholder="选择或输入新标签" style="width: 100%">
          <el-option v-for="t in tags" :key="t" :label="t" :value="t" />
        </el-select>
      </el-form-item>
      <el-form-item label="到期时间">
        <el-date-picker v-model="form.due_date" type="datetime"
                        placeholder="选填" style="width: 100%" />
      </el-form-item>
      <el-form-item label="提醒时间">
        <el-select v-model="remindPreset" placeholder="不提醒" style="width: 140px"
                   @change="applyPreset">
          <el-option label="不提醒" value="none" />
          <el-option label="提前15分钟" value="15" />
          <el-option label="提前30分钟" value="30" />
          <el-option label="提前1小时" value="60" />
          <el-option label="自定义" value="custom" />
        </el-select>
        <el-date-picker v-if="remindPreset === 'custom'" v-model="form.remind_at"
                        type="datetime" style="width: calc(100% - 150px); margin-left: 10px" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>
<script setup>
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { api } from "../api";
import { useTodos } from "../composables/useTodos";

const props = defineProps({ modelValue: Boolean, todo: Object });
const emit = defineEmits(["update:modelValue", "saved"]);
const { tags } = useTodos();
const form = ref({});
const remindPreset = ref("none");

watch(() => props.modelValue, (open) => {
  if (open) {
    form.value = props.todo
      ? { ...props.todo }
      : { title: "", description: "", priority: "medium", tags: [], due_date: null, remind_at: null };
    remindPreset.value = "custom";
  }
});

const applyPreset = (v) => {
  if (v === "none") form.value.remind_at = null;
  else if (v !== "custom" && form.value.due_date) {
    form.value.remind_at = new Date(new Date(form.value.due_date).getTime() - Number(v) * 60000);
  }
};

const save = async () => {
  if (!form.value.title?.trim()) { ElMessage.warning("标题必填"); return; }
  const payload = { ...form.value, title: form.value.title.trim() };
  if (props.todo) await api.updateTodo(props.todo.id, payload);
  else await api.createTodo(payload);
  emit("update:modelValue", false);
  emit("saved");
};
</script>
```

- [ ] **Step 2: 浏览器验证**：新建（含标签 allow-create）、编辑回填、提醒快捷选项、标题必填校验（对应 US-001/US-005）
- [ ] **Step 3: Commit** `feat: 新建编辑表单`

---

### Task 10: 状态栏与完成交互收尾

**Files:**
- Create: `frontend/src/components/StatusBar.vue`
- Modify: `useTodos.js`（确保 complete 后刷新统计）

- [ ] **Step 1: StatusBar.vue**

```vue
<template>
  <div style="display:flex; gap:24px; align-items:center; padding:0 16px; font-size:13px; color:#666">
    <span>待办：{{ stats.total }}</span>
    <span>已完成：{{ stats.completed }}</span>
    <span :style="stats.overdue ? 'color:#f56c6c' : ''">逾期：{{ stats.overdue }}</span>
  </div>
</template>
<script setup>
import { useTodos } from "../composables/useTodos";
const { stats } = useTodos();
</script>
```

- [ ] **Step 2: 浏览器验证**：完成勾选后状态栏计数实时变化（US-004/US-008）
- [ ] **Step 3: Commit** `feat: 状态栏`

---

### Task 11: Electron 桌面壳

**Files:**
- Create: `desktop/package.json`、`desktop/main.js`
- Consumes: 后端（开发模式 `python -X utf8 start_dev.py`；生产模式 `todo_backend.exe`）

- [ ] **Step 1: package.json**

```json
{
  "name": "todo-reminder-desktop",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": { "start": "electron ." },
  "devDependencies": { "electron": "^33.0.0" }
}
```

- [ ] **Step 2: main.js**（原型已验证的链路 + 窗口可最小化 + 退出清理）

```javascript
const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const http = require("http");

const IS_PACKAGED = !process.defaultApp; // electron-builder 运行时为 true
const BACKEND_EXE = path.join(process.resourcesPath, "backend", "todo_backend.exe");
const PYTHON = "D:\\developTools\\python\\python3.14.5\\python.exe";
const DEV_SERVER = path.join(__dirname, "..", "backend", "start_dev.py");
const PORT_FILE = path.join(path.dirname(BACKEND_EXE), "..", "backend.port");

let backendProc = null;

function startBackend() {
  const cmd = IS_PACKAGED ? BACKEND_EXE : PYTHON;
  const args = IS_PACKAGED ? [] : ["-X", "utf8", DEV_SERVER];
  backendProc = spawn(cmd, args, { windowsHide: true });
}

function waitHealthy(port, timeoutMs = 15000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const poll = () => {
      const req = http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
        res.resume();
        res.statusCode === 200 ? resolve(port) : retry();
      });
      req.on("error", retry);
      req.setTimeout(1000, () => { req.destroy(); retry(); });
    };
    const retry = () => (Date.now() - start > timeoutMs
      ? reject(new Error("health timeout"))
      : setTimeout(poll, 300));
    poll();
  });
}

async function createWindow() {
  startBackend();
  let port = null;
  for (let i = 0; i < 100; i++) {
    if (fs.existsSync(PORT_FILE)) {
      port = parseInt(fs.readFileSync(PORT_FILE, "utf-8").trim(), 10);
      break;
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  if (!port) throw new Error("backend port file not found");
  await waitHealthy(port);

  const win = new BrowserWindow({ width: 1000, height: 700, title: "待办助手" });
  win.loadURL(`http://127.0.0.1:${port}`);
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => {
  if (backendProc) spawn("taskkill", ["/PID", String(backendProc.pid), "/T", "/F"], { windowsHide: true });
  app.quit();
});
```

- [ ] **Step 3: 验证**：`npm install`（记得 ELECTRON_MIRROR）→ `npm start`，桌面窗口显示完整应用，最小化后 winotify 测试通知仍可弹出，关闭窗口任务管理器无残留 python/electron 进程
- [ ] **Step 4: Commit** `feat: Electron 桌面壳`

---

### Task 12: 打包链路（一键 EXE）

**Files:**
- Create: `backend/todo_backend.spec`（PyInstaller 配置）
- Create: `desktop/package.json`（补 build 配置）
- Create: `scripts/build.ps1`

- [ ] **Step 1: PyInstaller 打包后端**

```
D:\developTools\python\python3.14.5\python.exe -m pip install pyinstaller --quiet
D:\developTools\python\python3.14.5\python.exe -m PyInstaller --onedir --name todo_backend --noconsole backend/start_dev.py
```

（--onedir 启动更快；产物 `dist/todo_backend/`，含 todo_backend.exe）

- [ ] **Step 2: 前端构建**

```
cd frontend && npm run build
```

构建产物 `frontend/dist/` 拷入后端可执行目录（runner.py 的 frontend_dist 路径在打包 spec 中对齐，或运行时以 exe 同目录解析）。

- [ ] **Step 3: electron-builder 配置**（desktop/package.json 增加）

```json
"build": {
  "appId": "com.limw.todoreminder",
  "productName": "待办助手",
  "files": ["main.js"],
  "extraResources": [{ "from": "../dist/todo_backend", "to": "backend" },
                     { "from": "../frontend/dist", "to": "backend/frontend_dist" }],
  "win": { "target": ["portable"] }
}
```

- [ ] **Step 4: scripts/build.ps1**（固化镜像 + 四步链）

```powershell
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
# 1. 前端构建
Set-Location frontend; npm run build; Set-Location ..
# 2. 后端打包
& D:\developTools\python\python3.14.5\python.exe -m PyInstaller --onedir --name todo_backend --noconsole backend/start_dev.py --distpath dist
# 3. 拷前端产物进后端目录
Copy-Item -Recurse -Force frontend/dist dist/todo_backend/frontend_dist
# 4. electron-builder
Set-Location desktop; npm run build; Set-Location ..
```

- [ ] **Step 5: 验证**：双击 portable EXE → 窗口出现 ≤5 秒；新建待办设提醒 1 分钟后 → Toast 弹出；关闭窗口 → 任务管理器无残留（US-007 全部验收）
- [ ] **Step 6: Commit** `feat: 打包链路`

---

### Task 13: 联调验收与交接

**Files:**
- Modify: `README.md`（运行/打包说明）
- Create: `docs/handoff.md`（阶段 6 用 handoff 技能生成）

- [ ] **Step 1: 全量测试** `python -X utf8 -m pytest backend/tests/ -v` 全绿
- [ ] **Step 2: 端到端走查**（对照 PRD US-001~US-008 验收清单逐项打勾）
- [ ] **Step 3: 干净环境冒烟**（另一台机器或新用户目录双击 EXE）
- [ ] **Step 4: Commit + push**，进入阶段 6 交接

---

## 自检记录（Self-Review）

1. **规格覆盖**：PRD 9 条功能需求 FR-1~FR-9 全部落到 Task 1-12；US-001~008 在 Task 8-12 的浏览器验证步骤覆盖；CONTEXT.md 五条边界规则在 Task 3 测试显式覆盖（无due_date/已完成不逾期）与 Task 5（一次性/补发）。
2. **占位符扫描**：无 TBD/TODO；Task 3 标签筛选标注了实现细节的落地方式（原生 text SQL）。
3. **类型一致性**：todo_service 返回 dict 字段与 TodoOut 一致；ReminderEngine 构造签名 (service, notifier, now) 在 Task 5/6 一致；useTodos 单例化提示在 Task 8 明确。
