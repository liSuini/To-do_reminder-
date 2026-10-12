# 架构设计文档：待办助手（To-do Reminder）

- 日期：2026-10-12
- 依据：PRD（tasks/prd-todo-assistant.md）+ 需求拆分（docs/requirements/）+ ADR 0001–0003
- 术语：遵循 CONTEXT.md 领域术语表

## 1. 总体架构

```
┌─────────────────────────────────────────────────────┐
│                Electron 主进程（main.js）              │
│  职责：窗口生命周期 + 后端子进程管理                     │
│  ├─ spawn 后端（dev: uvicorn / prod: todo_backend.exe）│
│  ├─ 轮询 GET /api/health 直至 200                     │
│  ├─ 读取 backend.port 文件获取实际端口                 │
│  ├─ BrowserWindow 加载 http://localhost:{port}       │
│  └─ 退出时 taskkill 后端子进程                         │
├─────────────────────────────────────────────────────┤
│              FastAPI 后端（Python）                    │
│  ┌────────────── web 层（薄适配层）──────────────┐    │
│  │  routers/todos.py    HTTP ↔ service 翻译      │    │
│  │  routers/system.py   /api/health              │    │
│  └──────────┬───────────────────────────────────┘    │
│             │                                         │
│  ┌──────────▼─────────────────┐ ┌──────────────────┐ │
│  │      todo_service          │ │  reminder_engine  │ │
│  │  （深模块：全部业务规则）      │ │  （深模块：调度）    │ │
│  │  CRUD/视图/排序/统计        │ │  扫描/触发/补发     │ │
│  └──────────┬─────────────────┘ └────────┬─────────┘ │
│             │                            │           │
│  ┌──────────▼──────────┐  ┌──────────────▼─────────┐ │
│  │   db（SQLAlchemy）    │  │ notification_gateway   │ │
│  │   todos 表 + 会话工厂  │  │ （接缝：winotify/测试）  │ │
│  └─────────────────────┘  └────────────────────────┘ │
│  runner.py：组装一切（应用工厂 + 端口探测 + 静态托管）    │
├─────────────────────────────────────────────────────┤
│          Vue3 前端（构建为静态文件，由 FastAPI 托管）     │
│  api.js（薄）→ useTodos（组合式状态）→ 组件               │
│  Sidebar / TodoList / TodoCard / TodoForm / StatusBar  │
└─────────────────────────────────────────────────────┘
```

## 2. 后端模块设计（深模块原则）

### 2.1 todo_service — 核心业务模块（深）

**接缝**：service 公开函数集合（不暴露 ORM 模型，进出均为 dict/Pydantic Schema）。

**接口**（调用方只需知道这些）：

```python
create_todo(data: TodoCreate) -> Todo
update_todo(todo_id: int, data: TodoUpdate) -> Todo | None
delete_todo(todo_id: int) -> bool
set_completed(todo_id: int, completed: bool) -> Todo | None
query_todos(view: View, tag: str|None, priority: Priority|None, status: Status|None) -> list[Todo]
get_stats(view: View) -> Stats       # {total, completed, overdue}
get_tag_names() -> list[str]        # 从现有待办派生标签列表
```

**隐藏的实现复杂度**：
- 视图边界计算（今日 00:00–23:59、本周周一至周日、逾期=due<今日 且 pending）
- 无 due_date 的待办仅出现在"全部"视图
- 排序规则（priority 降序 + due_date 升序，None 排最后）
- 标签筛选的 JSON1 查询（`json_each`）
- 领域不变量（completed_at 与 status 联动）

**测试面**：内存 SQLite + 直接调 service 函数，无需 HTTP。

### 2.2 reminder_engine — 提醒调度模块（深）

**接缝**：三个函数 + 一个注入的通知网关 + 一个注入的时钟。

```python
class ReminderEngine:
    def __init__(self, service, notifier: Notifier, now: Callable[[], datetime]): ...
    def scan_and_fire(self) -> int      # 扫描到期提醒→通知→标记，返回触发数
    def backfill_missed(self) -> int    # 启动时补发错过的提醒（按 due 降序）
    def start(self) / stop()           # APScheduler 30s 周期接线（可独立于测试）
```

**隐藏的实现复杂度**：
- "到期"判定（remind_at ≤ now 且未触发且待办未完成/未删除）
- 一次性触发保证（reminded 标记持久化）
- 错过补发只补一次（补发后同样标记）
- 单条失败不影响后续（逐条 try/except + 日志）

**注入依赖 = 真接缝**：`now()` 可替换为假时钟（测试确定性），`notifier` 可替换为 Spy（断言通知内容而无需真实弹窗）。

### 2.3 notification_gateway — 通知网关（真接缝，两适配器）

```python
class Notifier(Protocol):
    def send(self, title: str, body: str) -> None

class WinotifyNotifier:    # 生产适配器：winotify Toast
class SpyNotifier:         # 测试适配器：记录调用
```

两个适配器使该接缝成立（ADR-0003 的落点）。

### 2.4 web 层 — 刻意做薄

FastAPI router 只做 HTTP ↔ service 的翻译：解析参数、调 service、返回 JSON/422。不写业务规则（规则全在 todo_service，一处修复全局生效）。

### 2.5 runner.py — 组装根

应用工厂：创建 FastAPI 实例、挂载路由、静态文件托管（Vue dist）、启动 APScheduler、启动时执行 backfill_missed()、**端口探测**（8000 被占则递增探测，将实际端口写入 `backend.port` 文件供 Electron 读取）。入口同时服务两种运行形态（uvicorn 直跑 / PyInstaller 打包），无分支差异。

## 3. 前端模块设计

| 模块 | 类型 | 职责 |
|------|------|------|
| `api.js` | 薄适配 | fetch 封装（baseURL 从注入获取），无状态 |
| `useTodos.js` | 状态组合式函数 | 视图状态、待办列表、加载/刷新动作、统计——前端唯一有"策略"的地方 |
| `Sidebar.vue` | 展示组件 | 视图切换 + 标签筛选（标签列表来自 api） |
| `TodoList.vue` / `TodoCard.vue` | 展示组件 | 列表渲染、优先级色块、空状态 |
| `TodoForm.vue` | 表单组件 | 新建/编辑复用（传 todo 即编辑模式），标签输入建议，提醒快捷选项 |
| `StatusBar.vue` | 展示组件 | 当前视图计数 |

组件不直接调 api，一律经 `useTodos`（状态与动作同源，刷新逻辑一处）。

## 4. 关键数据流

**新建待办**：TodoForm → useTodos.create() → POST /api/todos → todo_service.create → SQLite → 刷新列表与统计

**提醒触发**（每 30 秒）：APScheduler → reminder_engine.scan_and_fire() → 查询 remind_at≤now 未触发且 pending → WinotifyNotifier.send(标题+截止时间) → 标记 reminded

**启动补发**：runner 启动 → backfill_missed() → 同上但一次性处理全部错过项

**Electron 启动序列**：main.js → spawn 后端 → 轮询 /api/health（200 即就绪）→ 读 backend.port → 加载窗口

**退出清理**：window-all-closed → taskkill /T /F 子进程树（防止 uvicorn 子进程残留）→ app.quit

## 5. 错误处理

| 场景 | 处理 |
|------|------|
| 请求校验失败 | FastAPI 自动 422，前端表单展示错误 |
| 提醒单条发送失败 | try/except + 日志，不中断调度循环 |
| 后端端口被占用 | runner 探测下一个可用端口，写 backend.port |
| Electron 退出但子进程残留 | taskkill /T /F 兜底（ADR-0001 风险缓解） |
| 数据库并发写 | SQLite WAL 模式 + 单进程场景，冲突面极小 |

## 6. 测试策略

| 层 | 方式 | 工具 |
|----|------|------|
| todo_service | 直接函数调用 + 内存 SQLite | pytest |
| reminder_engine | 假时钟 + SpyNotifier，不依赖 Windows | pytest |
| API 层 | TestClient 集成测试（覆盖 CRUD/视图/校验异常） | pytest + httpx |
| 前端 | 按验收标准浏览器人工验证（开发模式） | — |
| 打包产物 | 干净环境双击冒烟：启动≤5s、通知弹出、退出无残留进程 | 手动 |

**测试纪律**：测试穿过公开接口（service 函数 / HTTP），不测实现内部；reminder_engine 通过注入的 now/notifier 接缝测试，不在测试中弹真实通知。

## 7. 目录结构

```
To-do_reminder/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy Todo 模型
│   │   ├── schemas.py           # Pydantic 请求/响应 Schema
│   │   ├── database.py          # engine/session 工厂
│   │   ├── config.py            # 配置（端口、DB 路径、扫描间隔）
│   │   ├── services/
│   │   │   ├── todo_service.py  # 深模块：CRUD/视图/排序/统计
│   │   │   └── reminder_engine.py # 深模块：调度/补发
│   │   ├── notify/
│   │   │   └── winotify_notifier.py  # 接缝适配器
│   │   ├── routers/
│   │   │   ├── todos.py         # 薄 HTTP 层
│   │   │   └── system.py        # /api/health
│   │   └── runner.py            # 组装根（应用工厂+端口探测）
│   ├── tests/
│   │   ├── test_todo_service.py
│   │   ├── test_reminder_engine.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── start_dev.py             # 开发模式入口（uvicorn 直跑）
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── composables/useTodos.js
│   │   ├── components/…         # Sidebar/TodoList/TodoCard/TodoForm/StatusBar
│   │   ├── App.vue
│   │   └── main.js
│   ├── vite.config.js
│   └── package.json
├── desktop/                     # Electron 壳
│   ├── main.js
│   ├── package.json
│   └── (build 资源引用 backend 产物)
├── scripts/
│   └── build.ps1               # 一键打包链路
├── docs/ …（现有文档）
├── CONTEXT.md
└── README.md
```

## 8. 设计原则备注

- **深模块**：todo_service 与 reminder_engine 各自把复杂度关进小接口（5–7 个方法）；web 层刻意薄
- **真接缝才建**：通知网关（两个适配器）、时钟注入（测试确定性）；不引入"未来可能替换"的假想接缝
- **组装唯一**：runner.py 是唯一知道"一切如何拼起来"的地方；Electron main.js 是进程层的组装根
- **YAGNI**：无 Pinia/Router（单页够用）、无独立标签表（ADR-0002）、无 WebSocket（30 秒轮询前端足够）
