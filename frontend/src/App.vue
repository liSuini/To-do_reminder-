<template>
  <el-container class="app">
    <el-aside width="200px">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-main>
        <TodoList />
      </el-main>
      <el-footer height="36px">
        <StatusBar />
      </el-footer>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from "./components/Sidebar.vue";
import TodoList from "./components/TodoList.vue";
import StatusBar from "./components/StatusBar.vue";
import { useTodos } from "./composables/useTodos";
import { onMounted } from "vue";

const { refresh } = useTodos();
onMounted(refresh);
</script>
