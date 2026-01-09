<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="router.back()"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">待办事项</div>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <!-- 添加待办输入框 -->
        <TodoInput class="mb-6" />

        <!-- 待办列表 -->
        <TodoList
          :todos="sortedTodos"
          @toggle="handleToggle"
          @update-title="handleUpdateTitle"
          @delete="handleDelete"
          @delete-group="handleDeleteGroup"
          @delete-item="handleDeleteItem"
          @pin="handlePin"
          @add-group-item="handleAddGroupItem"
          @update-item-title="handleUpdateItemTitle"
          @toggle-item="handleToggleItem"
          :show-completed="true"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useDataStore } from "../stores/data";
import TodoList from "../components/TodoList.vue";
import TodoInput from "../components/TodoInput.vue";
import { useRouter } from "vue-router";

const router = useRouter();

const emit = defineEmits<{
  back: [];
}>();

const data = useDataStore();

// 排序后的待办列表（按置顶优先，然后按创建时间倒序，最新的在上面）
const sortedTodos = computed(() => {
  return [...data.todos].sort((a, b) => {
    // 置顶的在前
    if (a.is_pinned && !b.is_pinned) return -1;
    if (!a.is_pinned && b.is_pinned) return 1;
    // 然后按创建时间倒序
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();
    return timeB - timeA;
  });
});

const handleToggle = (id: number) => {
  data.toggleTodo(id);
};

const handleUpdateTitle = (id: number, title: string) => {
  data.updateTodo(id, { title });
};

const handleDelete = (id: number) => {
  data.removeTodo(id);
};

const handleDeleteGroup = (id: number) => {
  data.removeTodo(id);
};

const handleDeleteItem = (id: number) => {
  data.removeTodo(id);
};

const handlePin = (id: number) => {
  data.togglePinTodo(id);
};

const handleAddGroupItem = (groupId: number) => {
  data.addTodo("新建待办", groupId);
};

const handleUpdateItemTitle = (id: number, title: string) => {
  data.updateTodo(id, { title });
};

const handleToggleItem = (id: number) => {
  data.toggleTodo(id);
};
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
</style>
