<template>
  <el-card class="todo-card" shadow="hover" :class="[todo.priority, { done: todo.status === 'completed' }]">
    <div class="row">
      <el-checkbox
        :model-value="todo.status === 'completed'"
        @change="onComplete"
      />
      <span class="priority-dot" :class="todo.priority" :title="priorityLabel" />
      <span class="title">{{ todo.title }}</span>
      <div class="tags">
        <el-tag v-for="t in todo.tags" :key="t" size="small" type="info">
          {{ t }}
        </el-tag>
      </div>
      <span v-if="todo.due_date" class="due">🕐 {{ fmt(todo.due_date) }}</span>
      <span v-if="todo.status === 'completed' && todo.completed_at" class="completed-at">
        ✓ {{ fmt(todo.completed_at) }} 完成
      </span>
      <div class="actions">
        <el-button link size="small" @click="$emit('edit', todo)">编辑</el-button>
        <el-popconfirm title="删除该待办？" @confirm="onDelete">
          <template #reference>
            <el-button link size="small" type="danger">删除</el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>
    <div v-if="todo.description" class="description">{{ todo.description }}</div>
  </el-card>
</template>

<script setup>
import { computed } from "vue";
import { ElMessage } from "element-plus";
import { useTodos } from "../composables/useTodos";

const props = defineProps({ todo: Object });
defineEmits(["edit"]);

const { completeTodo, deleteTodo, refresh } = useTodos();

const priorityLabel = computed(
  () => ({ high: "高", medium: "中", low: "低" })[props.todo.priority] || ""
);

const onComplete = async (v) => {
  try {
    await completeTodo(props.todo.id, v);
  } catch {
    ElMessage.error("操作失败，请重试");
    refresh();
  }
};

const onDelete = async () => {
  try {
    await deleteTodo(props.todo.id);
    ElMessage.success("已删除");
  } catch {
    ElMessage.error("删除失败，请重试");
  }
};

const fmt = (d) =>
  new Date(d).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
</script>

<style scoped>
.todo-card {
  margin-bottom: 8px;
  border-radius: 8px;
}

.todo-card.done .title {
  text-decoration: line-through;
  color: #909399;
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.priority-dot.high { background: #f56c6c; }
.priority-dot.medium { background: #e6a23c; }
.priority-dot.low { background: #909399; }

.title {
  font-weight: 500;
}

.tags {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.due {
  color: #909399;
  font-size: 13px;
  margin-left: auto;
  white-space: nowrap;
}

.completed-at {
  color: #67c23a;
  font-size: 12px;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 2px;
}

.description {
  margin-top: 6px;
  margin-left: 32px;
  color: #909399;
  font-size: 13px;
  white-space: pre-wrap;
}
</style>
