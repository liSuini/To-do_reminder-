<template>
  <div class="status-bar">
    <span class="item">待办：<b>{{ stats.total }}</b></span>
    <span class="item">已完成：<b class="ok">{{ stats.completed }}</b></span>
    <span class="item" :class="{ danger: stats.overdue > 0 }">
      逾期：<b>{{ stats.overdue }}</b>
    </span>
  </div>
</template>

<script setup>
import { useTodos } from "../composables/useTodos";

const { stats } = useTodos();
</script>

<style scoped>
.status-bar {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #909399;
  width: 100%;
}

.item.danger {
  color: #f56c6c;
}

.ok {
  color: #67c23a;
}
</style>
