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
              placeholder="添加待办...（按回车创建组）"
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
import { ref, computed, onMounted, nextTick } from "vue";
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
    const event = new CustomEvent('focus-first-item', { detail: { groupId: group.id } });
    window.dispatchEvent(event);
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "创建失败");
  } finally {
    creatingGroup.value = false;
  }
};

// 处理切换完成状态
const handleToggle = async (id: number) => {
  try {
    const todo = data.findTodo(id);
    // 如果是组标题，需要同时切换所有子待办的状态
    if (todo && !todo.group_id && todo.group_items && todo.group_items.length > 0) {
      const newCompleted = !todo.completed;
      // 先切换组标题
      await data.updateTodo(id, { completed: newCompleted });
      // 然后切换所有子待办
      for (const item of todo.group_items) {
        if (item.completed !== newCompleted) {
          await data.updateTodo(item.id, { completed: newCompleted });
        }
      }
    } else {
      await data.toggleTodo(id);
    }
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "操作失败");
  }
};

// 处理更新标题
const handleUpdateTitle = async (id: number, title: string) => {
  try {
    await data.updateTodo(id, { title });
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "更新失败");
  }
};

// 处理删除单个待办
const handleDelete = async (id: number) => {
  try {
    await data.removeTodo(id);
    toast.success("删除成功");
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "删除失败");
  }
};

// 处理删除组
const handleDeleteGroup = async (id: number) => {
  const result = await confirm.show({
    title: "确认删除",
    message: "确定要删除这个待办组吗？组内所有待办将被删除。",
    confirmText: "删除",
    cancelText: "取消",
    type: "danger",
  });
  
  if (result) {
    try {
      await data.removeTodo(id);
      toast.success("删除成功");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  }
};

// 处理添加组内待办
const handleAddGroupItem = async (groupId: number) => {
  try {
    await data.addTodo("", groupId);
    // 等待数据更新和 DOM 渲染
    await nextTick();
    await nextTick(); // 多等待一个 tick
    // watch 会自动处理聚焦，这里不需要额外的事件
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "添加失败");
  }
};

// 处理更新组内待办标题
const handleUpdateItemTitle = async (id: number, title: string) => {
  try {
    await data.updateTodo(id, { title });
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "更新失败");
  }
};

// 处理切换组内待办完成状态
const handleToggleItem = async (id: number) => {
  try {
    await data.toggleTodo(id);
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "操作失败");
  }
};

// 处理删除组内待办
const handleDeleteItem = async (id: number) => {
  const result = await confirm.show({
    title: "确认删除",
    message: "确定要删除这个待办事项吗？",
    confirmText: "删除",
    cancelText: "取消",
    type: "danger",
  });
  
  if (result) {
    try {
      await data.removeTodo(id);
      toast.success("删除成功");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  }
};

// 处理置顶/取消置顶
const handlePin = async (id: number) => {
  try {
    await data.togglePinTodo(id);
    toast.success("置顶成功");
  } catch (error: any) {
    console.error("置顶操作失败:", error);
    toast.error(error.response?.data?.detail || "置顶失败，请重试");
  }
};

// 组件挂载时加载所有待办
onMounted(async () => {
  await data.fetchTodos(); // 不传参数，获取所有待办
});
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

