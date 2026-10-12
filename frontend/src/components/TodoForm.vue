<template>
  <el-dialog
    :model-value="modelValue"
    :title="todo ? '编辑待办' : '新建待办'"
    width="500px"
    @update:model-value="$emit('update:modelValue', $event)"
    @closed="resetForm"
  >
    <el-form :model="form" label-width="80px">
      <el-form-item label="标题" required>
        <el-input
          v-model="form.title"
          placeholder="要做什么？"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="详细内容">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="补充说明（选填）"
        />
      </el-form-item>

      <el-form-item label="优先级">
        <el-radio-group v-model="form.priority">
          <el-radio-button value="high">🔴 高</el-radio-button>
          <el-radio-button value="medium">🟡 中</el-radio-button>
          <el-radio-button value="low">⚪ 低</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="标签">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="选择已有标签或输入新标签"
          style="width: 100%"
        >
          <el-option v-for="t in tags" :key="t" :label="t" :value="t" />
        </el-select>
      </el-form-item>

      <el-form-item label="到期时间">
        <el-date-picker
          v-model="form.due_date"
          type="datetime"
          placeholder="选填"
          style="width: 100%"
          :default-time="defaultDueTime"
        />
      </el-form-item>

      <el-form-item label="提醒时间">
        <div class="remind-row">
          <el-select v-model="remindPreset" style="width: 150px" @change="applyPreset">
            <el-option label="不提醒" value="none" />
            <el-option label="提前15分钟" value="15" />
            <el-option label="提前30分钟" value="30" />
            <el-option label="提前1小时" value="60" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-date-picker
            v-if="remindPreset === 'custom'"
            v-model="form.remind_at"
            type="datetime"
            placeholder="选择提醒时刻"
            style="flex: 1"
          />
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useTodos } from "../composables/useTodos";

const props = defineProps({ modelValue: Boolean, todo: Object });
const emit = defineEmits(["update:modelValue", "saved"]);

const { tags, createTodo, updateTodo } = useTodos();

const form = ref({});
const remindPreset = ref("none");
const saving = ref(false);
const defaultDueTime = new Date(2000, 0, 1, 18, 0); // 默认 18:00

watch(
  () => props.modelValue,
  (open) => {
    if (open) resetForm();
  }
);

function resetForm() {
  if (props.todo) {
    form.value = {
      ...props.todo,
      // el-date-picker 需要 Date 对象；后端字符串按本地时间解析
      due_date: props.todo.due_date ? new Date(props.todo.due_date) : null,
      remind_at: props.todo.remind_at ? new Date(props.todo.remind_at) : null,
    };
    remindPreset.value = props.todo.remind_at ? "custom" : "none";
  } else {
    form.value = {
      title: "",
      description: "",
      priority: "medium",
      tags: [],
      due_date: null,
      remind_at: null,
    };
    remindPreset.value = "none";
  }
}

function applyPreset(v) {
  if (v === "none") {
    form.value.remind_at = null;
  } else if (v !== "custom") {
    if (!form.value.due_date) {
      ElMessage.warning("请先设置到期时间");
      return;
    }
    form.value.remind_at = new Date(
      new Date(form.value.due_date).getTime() - Number(v) * 60000
    );
  }
}

// Date → 本地时间字符串（YYYY-MM-DDTHH:mm:ss），避免 toISOString 转成 UTC
function toLocal(d) {
  if (!d) return null;
  const dt = new Date(d);
  const pad = (n) => String(n).padStart(2, "0");
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(
    dt.getHours()
  )}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
}

async function save() {
  const title = form.value.title?.trim();
  if (!title) {
    ElMessage.warning("标题必填");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      title,
      description: form.value.description || "",
      priority: form.value.priority,
      tags: form.value.tags || [],
      due_date: toLocal(form.value.due_date),
      remind_at: toLocal(form.value.remind_at),
    };
    if (props.todo) {
      await updateTodo(props.todo.id, payload);
      ElMessage.success("已更新");
    } else {
      await createTodo(payload);
      ElMessage.success("已创建");
    }
    emit("update:modelValue", false);
    emit("saved");
  } catch {
    ElMessage.error("保存失败，请重试");
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.remind-row {
  display: flex;
  gap: 8px;
  width: 100%;
}
</style>
