# 12: 打包链路 EXE

**What to build:** 最终交付形态——一键脚本完成"前端构建→PyInstaller 后端→静态文件嵌入→electron-builder"四步，产出双击即用的 Windows portable EXE。

**Blocked by:** 05 提醒引擎、08 待办列表与视图切换、09 新建/编辑表单、10 状态栏与完成交互、11 Electron 桌面壳

**Status:** ready-for-agent

- [ ] PyInstaller --onedir --noconsole 打包 start_dev.py 为 todo_backend.exe
- [ ] 前端 dist 拷入后端目录并被 runner 静态托管
- [ ] electron-builder extraResources 携带后端，win target=portable
- [ ] build.ps1 固化 ELECTRON_MIRROR 镜像（npmmirror）
- [ ] 双击 EXE：启动到可交互 ≤5 秒
- [ ] 双击 EXE：设 1 分钟提醒，Toast 正常弹出；关闭窗口无残留进程（对应 US-007）
