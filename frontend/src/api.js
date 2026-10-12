// API 薄适配层：fetch 封装，无状态；同源访问（开发模式经 vite proxy）
async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

export const api = {
  listTodos: (params) =>
    request(`/api/todos?${new URLSearchParams(params)}`),
  getTodo: (id) => request(`/api/todos/${id}`),
  createTodo: (data) =>
    request("/api/todos", { method: "POST", body: JSON.stringify(data) }),
  updateTodo: (id, data) =>
    request(`/api/todos/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteTodo: (id) => request(`/api/todos/${id}`, { method: "DELETE" }),
  completeTodo: (id, completed) =>
    request(`/api/todos/${id}/complete`, {
      method: "PATCH",
      body: JSON.stringify({ completed }),
    }),
  getTags: () => request("/api/tags"),
  getStats: (view) => request(`/api/stats?view=${view}`),
};
