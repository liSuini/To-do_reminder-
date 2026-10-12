# 待办助手 (To-do Reminder)

纯个人使用的 Windows 桌面待办管理与提醒工具。

## 功能

- **新建每日待办**：标题 / 内容 / 优先级（高中低）/ 标签 / 到期时间 / 提醒时间（提前15/30/60分钟或自定义）
- **定时提醒**：到期弹 Windows 原生 Toast 通知（右下角），窗口最小化不中断；应用没运行时错过的提醒下次启动补发一次
- **多视图**：今日 / 本周 / 已逾期 / 全部，左侧栏一键切换
- **标签分类**：输入即建标签，点标签筛选
- **状态栏**：当前视图的待办 / 已完成 / 逾期实时计数

## 技术栈

Electron（桌面壳）+ FastAPI + SQLAlchemy + SQLite + APScheduler + winotify（后端）+ Vue3 + Element Plus + Vite（前端）

## 快速开始

### 直接使用（推荐）

双击 `release\待办助手 1.0.0.exe`（portable 免安装）。数据保存在 `%APPDATA%\TodoReminder\todo.db`。

### 开发模式

```powershell
# 后端（终端1）
cd backend
python -X utf8 start_dev.py

# 前端（终端2）
cd frontend
npm run dev          # http://localhost:3000

# 或桌面壳一体化（自动拉起后端）
cd desktop
npm start
```

### 测试

```powershell
cd backend
python -X utf8 -m pytest tests/ -v    # 38 个测试
```

### 打包

```powershell
.\scripts\build.ps1    # 产出 release\待办助手 1.0.0.exe
```

> 打包脚本已内置 npmmirror 镜像（GitHub Releases 网络不可达环境必需）。

## 项目结构

```
backend/    Python 后端（API + 提醒调度 + 数据层）
frontend/   Vue3 前端
desktop/    Electron 壳（窗口 + 子进程管理）
scripts/    build.ps1 一键打包
docs/       设计文档 / ADR / 交接文档（handoff.md）
CONTEXT.md  领域术语表
```

## 文档

- 产品需求：`tasks/prd-todo-assistant.md`
- 架构设计：`docs/specs/2026-10-12-architecture-design.md`
- 领域规则：`CONTEXT.md`
- 交接文档：`docs/handoff.md`

## License

MIT
