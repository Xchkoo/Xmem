<template>
  <div class="flex items-center justify-between px-4 py-3 rounded-xl shadow min-h-[44px] group" :class="{ 'bg-yellow-50/30 border-2 border-yellow-400': todo.is_pinned, 'bg-white': !todo.is_pinned }">
    <div class="flex items-center gap-3 flex-1 min-w-0">
      <input 
        type="checkbox" 
        :checked="todo.completed" 
        @change="$emit('toggle', todo.id)" 
        class="flex-shrink-0 cursor-pointer"
      />
      
      <!-- 置顶图标（始终显示） -->
      <span v-if="todo.is_pinned" class="text-yellow-500 flex-shrink-0" title="已置顶">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      </span>
      
      <input
        v-model="editTitle"
        @blur="finishEdit"
        @keydown.enter="finishEdit"
        @keydown.esc="cancelEdit"
        ref="editInputRef"
        :class="{ 'line-through text-gray-400': todo.completed }"
        class="flex-1 text-sm bg-transparent border-none outline-none px-0 py-0 cursor-text focus:ring-0"
        :readonly="todo.completed"
      />
    </div>
    <div class="flex items-center gap-2 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
      <button
        v-if="!todo.completed"
        @click.stop="$emit('pin', todo.id)"
        class="p-1.5 rounded-md active:scale-95 transition-colors"
        :class="todo.is_pinned ? 'text-yellow-500 hover:text-yellow-600 hover:bg-yellow-50' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
        :title="todo.is_pinned ? '取消置顶' : '置顶'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :fill="todo.is_pinned ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      </button>
      <button 
        class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95 transition-opacity flex-shrink-0"
        @click="$emit('delete', todo.id)"
        title="删除待办"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import type { Todo } from "../stores/data";

const props = defineProps<{
  todo: Todo;
}>();

const emit = defineEmits<{
  toggle: [id: number];
  "update-title": [id: number, title: string];
  delete: [id: number];
  pin: [id: number];
}>();

const editTitle = ref(props.todo.title);
const editInputRef = ref<HTMLInputElement | null>(null);

// 监听 todo.title 的变化
watch(() => props.todo.title, (newTitle) => {
  editTitle.value = newTitle;
});

const finishEdit = () => {
  if (props.todo.completed) return; // 已完成的不能编辑
  if (editTitle.value.trim() && editTitle.value !== props.todo.title) {
    emit("update-title", props.todo.id, editTitle.value.trim());
  } else {
    // 如果内容为空或未改变，恢复原值
    editTitle.value = props.todo.title;
  }
};

const cancelEdit = () => {
  editTitle.value = props.todo.title;
};

onMounted(() => {
  editTitle.value = props.todo.title;
});
</script>

<style scoped>
/* 确保输入框没有黑边 */
input[type="text"] {
  @apply border-gray-200;
}
</style>

