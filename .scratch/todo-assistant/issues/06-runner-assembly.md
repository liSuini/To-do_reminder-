# 06: runner 组装根

**What to build:** 后端一键可跑——组装根把路由、数据库初始化、提醒调度、启动补发、静态文件托管、端口探测全部接起来，`python -X utf8 start_dev.py` 即得到全功能后端，Electron 靠 backend.port 文件发现实际端口。

**Blocked by:** 04 API 路由层、05 提醒引擎

**Status:** ready-for-agent

- [ ] create_app()：init_db + 路由挂载 + backfill_missed + APScheduler(30s)
- [ ] find_free_port()：8000 被占自动递增探测
- [ ] main()：端口写入 backend.port 文件，打印 BACKEND_READY
- [ ] frontend_dist 存在时挂载为静态根（供打包形态）
- [ ] start_dev.py 开发入口
- [ ] 测试：find_free_port 返回可绑定端口、create_app health 可达，全绿
