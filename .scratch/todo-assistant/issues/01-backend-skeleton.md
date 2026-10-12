# 01: 后端骨架与数据模型

**What to build:** 打下后端地基——Todo 数据模型可持久化到 SQLite，依赖装齐，pytest 可跑。完成后能通过测试创建并查询一条待办记录。

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] backend/ 目录结构建立（app/config.py、database.py、models.py、schemas.py）
- [ ] requirements.txt 含 fastapi/uvicorn/sqlalchemy/pydantic/apscheduler/winotify
- [ ] Todo 模型字段完整（title/description/priority/tags/due_date/remind_at/status/completed_at/reminded/created_at/updated_at）
- [ ] 测试：创建并查询待办，默认值正确（status=pending、reminded=False）
- [ ] pytest 全绿
