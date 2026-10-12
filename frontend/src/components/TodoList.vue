<template>
  <div class="todo-list">
    <div class="toolbar">
      <h2 class="view-title">{{ viewLabel }}</h2>
      <el-button type="primary" @click="openCreate">＋ 新建待办</el-button>
    </div>

    <el-empty v-if="!loading && !todos.length" description="暂无待办" />

    <div v-loading="loading" class="list">
      <TodoCard
        v-for="t in todos"
        :key="t.id"
        :todo="t"
        @edit="openEdit"
      />
    </div>

    <TodoForm v-model="dialogVisible" :todo="editing" @saved="onSaved" />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useTodos } from "../composables/useTodos";
import TodoCard from "./TodoCard.vue";
import TodoForm from "./TodoForm.vue";

const { todos, loading, currentView, currentTag, refresh } = useTodos();

const dialogVisible = ref(false);
const editing = ref(null);

const viewLabel = computed(() => {
  const map = { today: "今日待办", week: "本周待办", overdue: "已逾期", all: "全部待办" };
  const label = map[currentView.value] || "待办";
  return currentTag.value ? `${label} · ${currentTag.value}` : label;
});

const openCreate = () => {
  editing.value = null;
  dialogVisible.value = true;
};

const openEdit = (todo) => {
  editing.value = todo;
  dialogVisible.value = true;
};

const onSaved = () => refresh();
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.view-title {
  margin: 0;
  font-size: 18px;
}

.list {
  display: flex;
  flex-direction: column;
  min-height: 60px;
}
</style>
