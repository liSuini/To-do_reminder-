# 02: todo_service CRUD

**What to build:** 待办核心业务的深模块——创建、更新、删除、完成/取消完成四个操作，进出均为 dict 不暴露 ORM，测试用内存 SQLite 隔离。

**Blocked by:** 01 后端骨架与数据模型

**Status:** ready-for-agent

- [ ] create_todo / update_todo / delete_todo / set_completed 四个函数
- [ ] set_completed 联动 completed_at（完成时记录、取消时清空）
- [ ] 不存在的 id：update 返回 None、delete 返回 False
- [ ] 测试接缝：set_session_factory 可注入内存会话工厂
- [ ] 测试覆盖正常路径+缺失路径，全绿
