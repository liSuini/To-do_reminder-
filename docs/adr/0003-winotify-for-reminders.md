# ADR-0003：提醒通知由 Python 后端 winotify 触发，不走 Electron Notification API

- 状态：已接受
- 日期：2026-10-12

## 背景

双进程架构下，提醒通知有两个可选触发端：

1. **Python 后端**直接调 Windows Toast API（winotify 库）
2. 后端通过 WebSocket/轮询告知 Electron 前端，前端调 Electron 的 `Notification` API

## 决策

由 **Python 后端**用 winotify 直接弹出 Windows 原生 Toast 通知。

## 理由

- **链路短**：APScheduler 扫描到到期提醒 → 直接弹窗，一步完成。方案 2 需要后端→WebSocket→前端→Electron API 四段链路，任何一段断开就漏提醒
- **不依赖前端状态**：Electron 窗口最小化、页面未加载完成、渲染进程崩溃，都不影响提醒弹出
- **错过补发逻辑天然在后端**：启动补发时前端可能尚未就绪，方案 2 需等待前端加载完毕才能弹，引入时序问题
- winotify 使用 Windows 原生 Toast XML，无需管理员权限

## 后果

**正面**
- 提醒可靠性最高，测试面小（单端单测即可覆盖）
- Electron 壳保持"纯窗口管理"职责，不掺杂业务逻辑

**负面 / 限制**
- 通知点击无法直接唤起 Electron 主窗口（跨进程信号）→ 后续如需"点击通知跳转应用"，可在通知带 deep-link URL 或后端起本地信号端口，当前版本不做
- winotify 依赖 Windows 10+ 的 Toast 机制 → 与目标平台一致，可接受

## 被否方案

- **Electron Notification**：链路长、依赖前端存活、错过补发时序复杂
