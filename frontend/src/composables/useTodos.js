// useTodos — 前端唯一状态源（模块级单例：视图状态、待办列表、统计、动作）
import { reactive, ref } from "vue";
import { api } from "../api";

// ---- 单例状态（所有组件共享同一份） ----
const currentView = ref("today");
const currentTag = ref(null);
const todos = ref([]);
const tags = ref([]);
const stats = reactive({ total: 0, completed: 0, overdue: 0 });
const loading = ref(false);

async function refresh() {
  loading.value = true;
  try {
    const params = { view: currentView.value };
    if (currentTag.value) params.tag = currentTag.value;
    todos.value = await api.listTodos(params);
    Object.assign(stats, await api.getStats(currentView.value));
    tags.value = await api.getTags();
  } finally {
    loading.value = false;
  }
}

function switchView(view) {
  currentView.value = view;
  currentTag.value = null;
  return refresh();
}

function switchTag(tag) {
  currentTag.value = tag;
  return refresh();
}

function clearTag() {
  currentTag.value = null;
  return refresh();
}

async function createTodo(data) {
  await api.createTodo(data);
  return refresh();
}

async function updateTodo(id, data) {
  await api.updateTodo(id, data);
  return refresh();
}

async function deleteTodo(id) {
  await api.deleteTodo(id);
  return refresh();
}

async function completeTodo(id, completed) {
  await api.completeTodo(id, completed);
  return refresh();
}

export function useTodos() {
  return {
    currentView, currentTag, todos, tags, stats, loading,
    refresh, switchView, switchTag, clearTag,
    createTodo, updateTodo, deleteTodo, completeTodo,
  };
}
