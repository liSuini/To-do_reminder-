<template>
  <el-menu :default-active="currentView" @select="onView" class="sidebar-menu">
    <el-menu-item index="today">
      <span>📋 今日</span>
    </el-menu-item>
    <el-menu-item index="week">
      <span>📅 本周</span>
    </el-menu-item>
    <el-menu-item index="overdue">
      <span>⚠️ 已逾期</span>
    </el-menu-item>
    <el-menu-item index="all">
      <span>📁 全部</span>
    </el-menu-item>
  </el-menu>

  <div class="tag-section">
    <el-divider content-position="left">标签</el-divider>
    <div class="tag-list">
      <span v-if="!tags.length" class="tag-empty">暂无标签</span>
      <el-tag
        v-for="t in tags"
        :key="t"
        :effect="currentTag === t ? 'dark' : 'plain'"
        class="tag-item"
        @click="onTag(t)"
      >
        {{ t }}
      </el-tag>
    </div>
    <el-button v-if="currentTag" link size="small" @click="clearTag()">
      ✕ 清除筛选
    </el-button>
  </div>
</template>

<script setup>
import { useTodos } from "../composables/useTodos";

const { currentView, currentTag, tags, switchView, switchTag, clearTag } =
  useTodos();

const onView = (v) => switchView(v);
const onTag = (t) => switchTag(t);
</script>

<style scoped>
.sidebar-menu {
  border-right: none;
}

.tag-section {
  padding: 0 12px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.tag-item {
  cursor: pointer;
}

.tag-empty {
  color: #c0c4cc;
  font-size: 12px;
}
</style>
