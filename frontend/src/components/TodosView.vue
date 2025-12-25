<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="$emit('back')"
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
        <div class="mb-6 flex gap-2">
          <div class="flex-1 relative">
            <input 
              v-model="newTodoText"
              @keydown.enter.prevent="handleEnterKey"
              ref="newTodoInputRef"
              class="input flex-1 pr-12" 
              :placeholder="placeholderText"
              maxlength="50"
            />
            <span 
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none"
              :class="{ 'text-red-500': newTodoText.length > 50 }"
            >
              {{ newTodoText.length }}/50
            </span>
          </div>
          <button 
            class="btn primary" 
            @click="handleAddSingleTodo"
            :disabled="newTodoText.length > 50"
          >
            添加
          </button>
        </div>

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
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { useConfirmStore } from "../stores/confirm";
import TodoList from "./TodoList.vue";
import type { Todo } from "../stores/data";

const emit = defineEmits<{
  back: [];
}>();

const data = useDataStore();
const toast = useToastStore();
const confirm = useConfirmStore();

const newTodoText = ref("");
const newTodoInputRef = ref<HTMLInputElement | null>(null);
const creatingGroup = ref(false);

// 响应式窗口宽度
const windowWidth = ref(typeof window !== "undefined" ? window.innerWidth : 1024);

const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

const placeholderText = computed(() => {
  return windowWidth.value < 640 ? "添加待办..." : "添加待办...（按回车创建组）";
});

onMounted(() => {
  if (typeof window !== "undefined") {
    window.addEventListener("resize", handleResize);
    windowWidth.value = window.innerWidth;
  }
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", handleResize);
  }
});

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

// 添加单个待办事项
const handleAddSingleTodo = async () => {
  if (!newTodoText.value.trim()) {
    toast.warning("待办内容不能为空");
    return;
  }
  
  if (newTodoText.value.length > 50) {
    toast.warning("待办事项不能超过50字");
    return;
  }
  
  await data.addTodo(newTodoText.value);
  newTodoText.value = "";
};

// 处理回车键：创建组
const handleEnterKey = async () => {
  if (!newTodoText.value.trim()) return;
  if (creatingGroup.value) return;
  
  creatingGroup.value = true;
  try {
    const title = newTodoText.value.trim();
    newTodoText.value = "";
    
    // 创建组标题
    const group = await data.addTodo(title);
    
    // 创建组的第一个待办（空标题）
    const firstItem = await data.addTodo("", group.id);
    
    // 等待 DOM 更新后，聚焦到第一个待办的输入框
    await nextTick();
    // 通过事件通知 TodoGroup 组件聚焦第一个待办
    // 这里需要确保 TodoList 组件能接收到并处理这个事件
    // 由于 TodoList 内部也是渲染 TodoGroup，所以事件应该能传达
    const event = new CustomEvent('focus-first-item', { detail: { groupId: group.id } });
    window.dispatchEvent(event);
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "创建失败");
  } finally {
    creatingGroup.value = false;
  }
};

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
  data.addTodo("", groupId);
};

const handleUpdateItemTitle = (id: number, title: string) => {
  data.updateTodo(id, { title });
};

const handleToggleItem = (id: number) => {
  data.toggleTodo(id);
};
</script>

<style scoped>
.input {
  @apply w-full rounded-xl border border-gray-200 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm;
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
.shadow-float {
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.1);
}
</style>
