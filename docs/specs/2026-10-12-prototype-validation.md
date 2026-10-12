# 原型验证文档：待办助手关键链路

- 日期：2026-10-12
- 验证方式：轻量原型（代码位于 `.temp/`，用后即弃，不进入正式代码库）
- 结论：**两项关键风险点全部验证通过**

## 验证项 1：winotify Windows Toast 通知 ✅

**风险**：winotify 库能否在当前 Windows 环境正常弹出原生 Toast（Win10+ 依赖 Toast XML 机制）。

**方法**：`.temp/proto_winotify.py`，向隔离目录安装 winotify 后调用 `Notification.show()`。

**结果**：`TOAST_SENT_OK`，用户确认右下角看到"原型验证：待办提醒"弹窗，内容与音频（默认音效）均正常。

**结论**：ADR-0003 的通知方案可行，winotify 可直接用于生产。

## 验证项 2：Electron 拉起 Python 子进程并加载页面 ✅

**风险**：
1. Electron 主进程 spawn Python 子进程（uvicorn/FastAPI）能否正常拉起
2. 端口文件约定 + /api/health 轮询的就绪判断是否可靠
3. 窗口能否正确加载 localhost 页面

**方法**：`.temp/proto_server.py`（FastAPI + 端口探测 + 写 backend.port 文件）+ `.temp/proto_electron/main.js`（spawn → 等端口文件 → 轮询 health → BrowserWindow.loadURL）。

**结果**：
```
[backend] BACKEND_READY port=8000
[main] backend ready on port 8000
```
窗口正常显示"链路验证成功"页面，用户确认看到。端口探测、健康检查轮询、页面加载全链路约 3 秒内完成（满足 PRD 的 5 秒启动指标）。

**结论**：架构设计文档中定义的"Electron 启动序列"可行。

## 过程中发现的环境问题（已解决）

**Electron 二进制下载被墙**：`npm install electron` 后 `install.js` 需从 GitHub Releases 下载约 100MB 二进制，在你的网络环境下缓慢受阻。
**解决**：设置 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/` 后手动执行 `node install.js`，下载秒级完成。
**对正式开发的影响**：正式环境搭建与打包脚本中需固化此镜像配置（写入 npm 配置或脚本环境变量），否则 CI/新机器会卡在同一位置。

## 对后续开发的输入

1. 镜像配置写入 `scripts/build.ps1` 与开发环境说明（Electron 安装前置）
2. 端口文件约定（`backend.port`）验证可行，正式实现沿用
3. taskkill /T /F 进程树清理方式在原型中验证有效
4. Python 3.14.5 + fastapi/uvicorn/winotify 依赖组合在当前机器测试通过

## 原型处置

原型代码全部位于 `.temp/`（`proto_winotify.py`、`proto_server.py`、`proto_electron/`、`proto_deps/`），验证完成后即弃，不进入 Git 历史。正式编码阶段从零搭建 `backend/`、`frontend/`、`desktop/` 目录。
