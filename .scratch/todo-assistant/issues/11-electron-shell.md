# 11: Electron 桌面壳

**What to build:** 桌面化——Electron 主进程拉起后端子进程、健康检查轮询、加载页面，窗口可最小化（提醒不中断），关闭窗口可靠清理子进程树。

**Blocked by:** 06 runner 组装根、07 前端骨架

**Status:** ready-for-agent

- [ ] 开发模式 spawn `python -X utf8 start_dev.py`，生产模式 spawn 打包 exe（IS_PACKAGED 分支）
- [ ] 等 backend.port 文件出现 → 轮询 /api/health 就绪 → 加载页面
- [ ] 窗口最小化后 winotify 通知照常弹出
- [ ] 关闭窗口 taskkill /T /F 清理后端进程树，任务管理器无残留
- [ ] npm start 桌面窗口运行完整应用（对应 US-007 窗口行为）
