# 04: API 路由层

**What to build:** HTTP 对外服务——把 todo_service 与健康检查翻译成 REST 端点（刻意薄层，业务规则零重复）。API 层成为浏览器/桌面可调用的完整后端。

**Blocked by:** 03 视图/筛选/排序/统计

**Status:** ready-for-agent

- [ ] POST/GET/PUT/DELETE /api/todos，PATCH /api/todos/{id}/complete
- [ ] GET /api/todos?view=&tag=&priority=&status=（查询参数映射视图筛选）
- [ ] GET /api/tags、GET /api/stats?view=
- [ ] GET /api/health 返回 {"status":"ok"}
- [ ] 校验失败返回 422，缺失资源返回 404
- [ ] TestClient 集成测试全绿
