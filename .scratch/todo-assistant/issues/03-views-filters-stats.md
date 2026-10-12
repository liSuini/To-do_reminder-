# 03: 视图/筛选/排序/统计

**What to build:** 待办的"看"能力——四个视图（今日/本周/已逾期/全部）、标签/优先级/状态筛选、统一排序、当前视图统计、标签列表派生。落实 CONTEXT.md 的全部视图边界规则。

**Blocked by:** 02 todo_service CRUD

**Status:** ready-for-agent

- [ ] query_todos(view, tag, priority, status)：今日=00:00–23:59；本周=周一至周日；逾期=due<今日且 pending；全部=所有
- [ ] 无 due_date 的待办只出现在"全部"视图
- [ ] 排序：优先级降序 → due_date 升序 → 无日期最后
- [ ] get_stats(view)：total/completed/overdue，已完成永不逾期
- [ ] get_tag_names()：从现有待办派生去重标签
- [ ] 测试显式覆盖每条边界规则，全绿
