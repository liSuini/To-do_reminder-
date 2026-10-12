# 05: 提醒引擎

**What to build:** 到期提醒的核心——每 30 秒扫描 remind_at 到期且未触发的待办，通过通知网关弹 Windows Toast，一次性触发有持久化保证，启动时补发错过的提醒。测试用 SpyNotifier + 假时钟，不弹真实通知。

**Blocked by:** 01 后端骨架与数据模型

**Status:** ready-for-agent

- [ ] ReminderEngine(service, notifier, now) 构造注入
- [ ] scan_and_fire()：到期→通知→标记 reminded，返回触发数
- [ ] 单条通知失败不中断批量扫描（逐条 try/except+日志）
- [ ] backfill_missed()：启动补发，同样只补一次
- [ ] 已完成/已删除的待办不触发
- [ ] WinotifyNotifier 生产适配器 + SpyNotifier 测试适配器（真接缝）
- [ ] 测试覆盖：正常触发/一次性/未来不触发/已完成不触发/补发，全绿
