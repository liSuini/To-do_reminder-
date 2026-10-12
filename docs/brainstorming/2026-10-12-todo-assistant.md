# 头脑风暴记录：待办助手（To-do Reminder）

- 日期：2026-10-12
- 参与者：李鸣武（需求方）、星辰超级智能体（TeleAgent）
- 状态：需求澄清完成，方案已确认

## 1. 项目背景与目标

用户需要一个**纯个人使用**的待办助手，核心诉求：

1. 每日新建待办事项
2. 待办到期时通过 **Windows 系统通知**提醒
3. 打包成 **EXE 桌面软件**，双击即用，无需手动启动前后端

## 2. 需求澄清结论

| 问题 | 用户决策 |
|------|----------|
| 使用场景 | 纯个人使用（不做多用户） |
| 提醒方式 | Windows 系统通知（右下角 Toast 弹窗） |
| 功能范围 | 新建待办、定时提醒、优先级分类、标签分类、多视图切换 |
| 明确排除 | 完成统计、重复待办 |
| 技术栈 | FastAPI + Electron + Vue3 + Element Plus + SQLite |
| 交付形态 | EXE 打包，桌面窗口模式，窗口可最小化 |

## 3. 方案对比与选择

| 方案 | 组成 | 优点 | 缺点 | 结论 |
|------|------|------|------|------|
| A | FastAPI + PyWebView + Vue3 | 纯 Python 链路，轻量 | WebView2 依赖 | 未选 |
| **B** | **FastAPI + Electron + Vue3** | **桌面生态成熟，窗口控制丰富** | **体积大，构建链路需 Node.js** | **用户选定** |
| C | .NET 8 WPF + WebView2 + Vue3 | 原生 Windows 集成 | 技术栈切换 | 未选 |

用户明确选择方案 B（Electron），接受体积换取成熟的桌面体验。

## 4. 关键设计共识（逐段确认通过）

### 4.1 整体架构
- Electron 主进程启动时 spawn Python 后端子进程（PyInstaller 打包的 todo_backend.exe）
- FastAPI 提供 REST API 并托管 Vue3 静态文件
- Electron 加载 `http://localhost:8000`，退出时 kill 子进程

### 4.2 数据模型（todos 表）
- `title`（必填）、`description`、`priority`（high/medium/low）、`tags`（JSON 数组）
- `due_date`（截止时间）、`remind_at`（提醒触发时间，可为空）
- `status`（pending/completed）、`completed_at`、`created_at`、`updated_at`

### 4.3 API 设计
- 待办 CRUD：`POST/GET/PUT/DELETE /api/todos`、`PATCH /api/todos/{id}/complete`
- 视图查询：`GET /api/todos?view=today|week|overdue|all`
- 系统健康检查：`GET /api/health`（Electron 轮询判断后端就绪）

### 4.4 前端界面
- 左侧栏：视图切换（今日/本周/已逾期/全部）+ 标签筛选
- 主区域：待办卡片列表，优先级色块（🔴高/🟡中/⚪低）+ 标签 + 到期时间
- 底部状态栏：待办数/已完成数/逾期数
- 新建按钮弹出对话框：标题/内容/优先级/标签/到期时间/提醒时间

### 4.5 打包与通知
- 打包四步：Vue build → FastAPI+PyInstaller 打包 todo_backend.exe → electron-builder 打包安装包
- 通知机制：后端 APScheduler 每 30 秒扫描到期提醒，通过 **winotify** 直接弹 Windows Toast
- 选 winotify 而非 Electron Notification：链路更短、更可靠，不依赖前端是否运行
- 窗口行为：关闭=退出（kill 子进程），最小化=后台保持运行

## 5. 风险与注意事项

1. **Electron + Python 双进程协调**：需确保退出时可靠 kill 子进程，避免僵尸进程
2. **端口冲突**：8000 端口若被占用需自动换端口，Electron 动态获取后端实际端口
3. **PyInstaller 体积**：Python 后端打包后可能 40MB+，整体安装包预计 100MB+（用户已接受）
4. **首次启动延迟**：Python 后端启动需 1-3 秒，Electron 需轮询 health 接口后再加载页面
5. **构建环境**：用户机器需 Node.js（Electron 构建），python -m pip 装依赖，中文路径需 -X utf8

## 6. 下一步

- 产出 PRD（产品需求文档）
- 产出需求拆分文档
- 进入设计阶段（领域模型 + 架构设计）
