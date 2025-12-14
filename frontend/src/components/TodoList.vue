<template>
  <div class="space-y-2 custom-scrollbar" :class="compact ? 'max-h-[600px] overflow-y-auto pb-2' : ''">
    <!-- 未完成的待办 -->
    <div v-if="incompleteTodos.length > 0" class="space-y-2">
      <!-- 未完成分割线（只在待办页面显示，主界面不显示） -->
      <div v-if="!compact" class="mb-6 flex items-center gap-4">
        <div class="flex-1 border-t-2 border-gray-300"></div>
        <span class="text-sm font-medium text-gray-600 whitespace-nowrap">未完成</span>
        <div class="flex-1 border-t-2 border-gray-300"></div>
      </div>
      
      <template v-for="todo in incompleteTodos" :key="todo.id">
        <transition-group name="todo-item" tag="div">
          <!-- 如果是组 -->
          <TodoGroup
            v-if="todo.group_items && todo.group_items.length > 0"
            :key="`group-${todo.id}`"
            :todo="todo"
            @toggle="handleToggle"
            @update-title="handleUpdateTitle"
            @delete="handleDeleteGroup"
            @pin="handlePin"
            @add-item="handleAddGroupItem"
            @update-item-title="handleUpdateItemTitle"
            @toggle-item="handleToggleItem"
            @delete-item="handleDeleteItem"
          />
          <!-- 如果是单个待办 -->
          <TodoItem
            v-else
            :key="`item-${todo.id}`"
            :todo="todo"
            @toggle="handleToggle"
            @update-title="handleUpdateTitle"
            @delete="handleDelete"
            @pin="handlePin"
          />
        </transition-group>
      </template>
    </div>

    <!-- 已完成的待办 -->
    <div v-if="completedTodos.length > 0" class="space-y-2">
      <!-- 完成分割线 -->
      <div class="mb-6 flex items-center gap-4">
        <div class="flex-1 border-t-2 border-gray-300"></div>
        <span class="text-sm font-medium text-gray-600 whitespace-nowrap">完成</span>
        <div class="flex-1 border-t-2 border-gray-300"></div>
      </div>
      
      <template v-for="todo in completedTodos" :key="todo.id">
        <transition-group name="todo-item" tag="div">
          <!-- 如果是组 -->
          <TodoGroup
            v-if="todo.group_items && todo.group_items.length > 0"
            :key="`group-${todo.id}`"
            :todo="todo"
            @toggle="handleToggle"
            @update-title="handleUpdateTitle"
            @delete="handleDeleteGroup"
            @pin="handlePin"
            @add-item="handleAddGroupItem"
            @update-item-title="handleUpdateItemTitle"
            @toggle-item="handleToggleItem"
            @delete-item="handleDeleteItem"
          />
          <!-- 如果是单个待办 -->
          <TodoItem
            v-else
            :key="`item-${todo.id}`"
            :todo="todo"
            @toggle="handleToggle"
            @update-title="handleUpdateTitle"
            @delete="handleDelete"
            @pin="handlePin"
          />
        </transition-group>
      </template>
    </div>

    <!-- 空状态 -->
    <div v-if="todos.length === 0" class="text-center py-4 text-gray-400 text-sm">
      暂无待办事项
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import TodoItem from "./TodoItem.vue";
import TodoGroup from "./TodoGroup.vue";
import type { Todo } from "../stores/data";

const props = defineProps<{
  todos: Todo[];
  showCompleted?: boolean; // 是否显示已完成的待办
  compact?: boolean; // 紧凑模式（用于主页面）
}>();

const emit = defineEmits<{
  toggle: [id: number];
  "update-title": [id: number, title: string];
  delete: [id: number];
  "delete-group": [id: number];
  pin: [id: number];
  "add-group-item": [groupId: number];
  "update-item-title": [id: number, title: string];
  "toggle-item": [id: number];
  "delete-item": [id: number];
}>();

// 分离已完成和未完成的待办
const incompleteTodos = computed(() => {
  return props.todos.filter(t => !t.completed);
});

const completedTodos = computed(() => {
  if (!props.showCompleted) return [];
  return props.todos.filter(t => t.completed);
});

// 事件处理
const handleToggle = (id: number) => {
  // 后端已经处理了组标题勾选时自动勾选所有子待办的逻辑
  emit("toggle", id);
};

const handleUpdateTitle = (id: number, title: string) => {
  emit("update-title", id, title);
};

const handleDelete = (id: number) => {
  emit("delete", id);
};

const handleDeleteGroup = (id: number) => {
  emit("delete-group", id);
};

const handleAddGroupItem = (groupId: number) => {
  emit("add-group-item", groupId);
};

const handleUpdateItemTitle = (id: number, title: string) => {
  emit("update-item-title", id, title);
};

const handleToggleItem = (id: number) => {
  emit("toggle-item", id);
};

const handleDeleteItem = (id: number) => {
  emit("delete-item", id);
};

const handlePin = (id: number) => {
  emit("pin", id);
};
</script>

<style scoped>
/* 待办项过渡动画 */
.todo-item-enter-active,
.todo-item-leave-active {
  transition: all 0.3s ease;
}

.todo-item-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.todo-item-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.todo-item-move {
  transition: transform 0.3s ease;
}

/* 自定义滚动条样式 - 极简风格 */
.custom-scrollbar {
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent; /* Firefox: 滑块颜色 轨道颜色 */
}

/* Webkit 浏览器 (Chrome, Safari, Edge) */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px; /* 滚动条宽度 */
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent; /* 滚动条轨道背景透明 */
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5); /* 滚动条滑块颜色 - 浅灰色 */
  border-radius: 3px;
  border: none; /* 移除边框 */
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7); /* 悬停时稍深一点 */
}

/* 隐藏滚动条按钮（上下箭头） */
.custom-scrollbar::-webkit-scrollbar-button {
  display: none; /* 不显示上下箭头按钮 */
}
</style>

