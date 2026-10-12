# 交接文档：待办助手（To-do Reminder）

- 日期：2026-10-12
- 状态：**v1.0.0 交付完成**（全栈开发大师七阶段闭环走完）

## 一句话总结

FastAPI + Vue3 + Electron 的纯个人 Windows 桌面待办助手：新建待办（优先级/标签/到期时间/提醒时间）→ APScheduler 定时扫描 → winotify 弹 Windows 原生 Toast，最终打包为双击即用的 portable EXE。

## 当前状态与验证结论

| 验证项 | 结果 |
|--------|------|
| 后端 pytest | 38 passed（模型/CRUD/视图边界/提醒引擎/API 全覆盖） |
| 浏览器 UI 验证 | US-001~005、US-008 全部通过（新建/编辑/删除/视图切换/标签筛选/完成/统计） |
| 提醒端到端 | 真实触发过 Toast（创建 30 秒后调度扫描弹出并标记 reminded） |
| EXE 冒烟 | 双击运行、窗口正常、退出零残留进程、端口释放 |
| 数据持久化 | 跨重启验证通过（DB 在 %APPDATA%\TodoReminder\todo.db） |
| 启动耗时 | 实测约 8.7 秒（portable 自解压固有成本，见"已知限制"） |

## 目录结构与职责

```
backend/           Python 后端（FastAPI）
  app/config.py        配置（frozen 时 DB 落 %APPDATA%）
  app/database.py      SQLAlchemy engine/session
  app/models.py        Todo ORM（唯一核心表）
  app/schemas.py       Pydantic 校验
  app/services/todo_service.py     深模块：CRUD/视图/排序/统计
  app/services/reminder_engine.py  深模块：扫描/触发/补发
  app/notify/winotify_notifier.py  通知网关适配器（ADR-0003）
  app/routers/         薄 HTTP 层（todos + system/health）
  app/runner.py        组装根：端口探测+调度+静态托管
  start_dev.py         开发入口
  tests/               38 个测试
frontend/          Vue3 + Element Plus + Vite
  src/api.js           fetch 封装
  src/composables/useTodos.js  前端唯一状态源（单例）
  src/components/       Sidebar/TodoList/TodoCard/TodoForm/StatusBar
desktop/           Electron 壳
  main.js              spawn 后端+健康轮询+窗口管理+退出清理
scripts/build.ps1  一键打包（前端→PyInstaller→electron-builder）
release/           产物：待办助手 1.0.0.exe（portable，89.8MB）
docs/              阶段文档（brainstorming/adr/specs/plans/requirements）
CONTEXT.md         领域术语表（视图边界规则以此为准）
.scratch/todo-assistant/issues/  13 张任务单（全部完成）
```

## 关键决策（详见 docs/adr/）

1. **ADR-0001**：Electron+Python 双进程；关闭窗口 taskkill /T /F 清理进程树
2. **ADR-0002**：标签存 todos.tags JSON 列，SQLite json_each 筛选，不建关联表
3. **ADR-0003**：提醒由 Python 端 winotify 直弹 Toast，不走 Electron Notification

## 开发环境与命令

- Python：`D:\developTools\python\python3.14.5\python.exe`，一切 python 调用带 `-X utf8`
- 依赖已装全局（fastapi/uvicorn/sqlalchemy/apscheduler/winotify/pytest/httpx/pyinstaller）

```powershell
# 开发模式（两个终端）
cd backend ; python -X utf8 start_dev.py        # 后端 :8000（uvicorn）
cd frontend ; npm run dev                        # 前端 :3000（vite proxy /api→8000）

# 测试
cd backend ; python -X utf8 -m pytest tests/ -v

# 桌面壳开发模式
cd desktop ; npm start                            # 自动拉起后端+开窗口

# 一键打包（产出 release\待办助手 1.0.0.exe）
.\scripts\build.ps1
```

## 打包产物行为

- 双击 `release\待办助手 1.0.0.exe` → 自解压到 %TEMP% → 拉起内嵌 todo_backend.exe → 轮询 /api/health → 打开窗口
- 数据文件：`%APPDATA%\TodoReminder\todo.db`（portable 的 TEMP 目录退出即删，故 DB 固定在 APPDATA，已实测跨重启持久）
- 提醒：窗口最小化不影响；应用未运行期间错过的提醒，下次启动补发一次（CONTEXT.md 规则）

## 开发中踩过的坑（新会话必读）

1. **Electron/工具链下载被墙**：必须 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/`、`ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/`（已固化在 build.ps1）
2. **前端时区 Bug**：`JSON.stringify(Date)` 走 toISOString 转 UTC；TodoForm 已用 toLocal() 序列化为本地时间字符串
3. **端口文件竞态**：Electron 可能读到上一轮遗留 backend.port；已修为"spawn 时刻之后写入的端口文件才有效"（mtime 判定）
4. **portable 数据丢失**：DB 不能放 exe 旁（TEMP 退出即删），已改 %APPDATA%
5. **PS 5.1**：脚本勿用 `$ErrorActionPreference="Stop"` 配原生命令（npm stderr 误杀）；PyInstaller 重复构建需 `-y`
6. **SQLite 文件锁**：Windows 下删 .db 前须 `engine.dispose()`；测试前先停占用进程

## 已知限制与后续建议

- **启动约 9 秒**：portable 每次自解压 89.8MB 所致。要 ≤5 秒可改 electron-builder `win.target=nsis`（安装版，免解压），build.ps1 一行可切
- **无点击通知唤起窗口**：winotify 是 Python 端单向弹窗；如需"点通知跳应用"需加 deep link 或本地信号端口
- **无自动刷新**：外部改数据窗口不感知（无 WebSocket，YAGNI 取舍）
- **双实例**：同时开两个 EXE 共享同一 APPDATA DB，SQLite 能容忍但建议单实例（可后续加互斥锁）
- **未做**（PRD 明确排除）：完成统计图表、重复待办、多用户、云同步、开机自启

## 文档索引

- 需求：`tasks/prd-todo-assistant.md`、`docs/requirements/2026-10-12-requirement-breakdown.md`
- 设计：`CONTEXT.md`、`docs/specs/2026-10-12-architecture-design.md`、`docs/adr/0001-0003`
- 计划：`docs/plans/2026-10-12-todo-assistant-plan.md`、`.scratch/todo-assistant/issues/`
- 验证：`docs/specs/2026-10-12-prototype-validation.md`、本文件

## 建议后续会话调用的技能

- 改需求/加功能：brainstorming → 全栈流程对应阶段
- 修 bug：systematic-debugging
- 加测试：tdd / python-testing-patterns
- 改打包：直接编辑 scripts/build.ps1 与 desktop/package.json（本文档"打包产物行为"节）
