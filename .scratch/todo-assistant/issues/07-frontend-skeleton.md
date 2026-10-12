# 07: 前端骨架

**What to build:** 浏览器里的应用骨架——Vite+Vue3+Element Plus 三区布局（左侧栏/主区域/底部状态栏），api.js 封装与 useTodos 单例状态源就位，开发模式经 vite proxy 连后端。

**Blocked by:** None (can start immediately，可与后端并行)

**Status:** ready-for-agent

- [ ] Vite 脚手架 + Element Plus 引入
- [ ] App.vue 三区容器布局，铺满窗口高度
- [ ] api.js：listTodos/createTodo/updateTodo/deleteTodo/completeTodo/getTags/getStats
- [ ] useTodos.js 单例组合式函数（状态+动作同源）
- [ ] vite proxy /api → 127.0.0.1:8000
- [ ] npm run dev 页面正常渲染三区
