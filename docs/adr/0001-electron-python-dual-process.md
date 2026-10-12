# ADR-0001：Electron + Python 双进程桌面架构

- 状态：已接受
- 日期：2026-10-12

## 背景

待办助手需要以 Windows 桌面应用形态交付（双击 EXE、桌面窗口、可最小化、Windows 系统通知提醒）。技术栈上用户熟悉 FastAPI（后端）与 Vue3/Element Plus（前端），曾比较三种桌面化路径：

1. PyWebView + FastAPI（纯 Python 链路）
2. **Electron + FastAPI（双运行时）**
3. .NET 8 WPF + ASP.NET Core（全 .NET 链路）

## 决策

采用 **Electron + Python 双进程**架构：

- Electron 主进程负责窗口生命周期，启动时 spawn Python 后端子进程
- FastAPI 后端提供 REST API 并托管 Vue3 构建产物（静态文件）
- Electron 轮询 `/api/health` 判断后端就绪后加载页面
- 关闭窗口时主进程终止后端子进程
- 发布时：Python 后端先经 PyInstaller 编译为独立 exe，再由 electron-builder 打包为整体安装包

## 理由

- 用户明确选择 Electron，接受体积换取成熟的桌面窗口能力与生态
- 前后端技术栈与用户既有项目（BidAlert）完全一致，零额外学习成本
- PyWebView 虽更轻量，但窗口控制、托盘、通知、打包生态均弱于 Electron

## 后果

**正面**
- 桌面体验成熟稳定，窗口/托盘/通知 API 开箱即用
- 后端可脱离 Electron 独立开发调试（uvicorn + 浏览器）

**负面 / 风险**
- 双运行时：安装包体积 100MB+；需管理两个构建链路（pip + npm）
- 进程生命周期复杂：必须保证 Electron 退出时可靠 kill 后端子进程，避免残留进程
- 启动延迟：后端子进程启动需 1–3 秒，需要就绪轮询机制

**缓解**
- 用 `proc.exit()` + Windows `taskkill` 双保险清理子进程
- 后端端口被占用时自动探测可用端口并写入约定文件供 Electron 读取

## 被否方案

- **PyWebView**：用户不选
- **WPF + ASP.NET Core**：技术栈切换，放弃既有 FastAPI 资产
