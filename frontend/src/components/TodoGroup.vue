<template>
  <div class="bg-white rounded-xl shadow overflow-hidden" :class="{ 'border-2 border-yellow-400 bg-yellow-50/30': todo.is_pinned, 'border border-gray-100': !todo.is_pinned }">
    <!-- 组标题栏 -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 group" :class="{ 'bg-yellow-50/50': todo.is_pinned }">
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
          @blur="finishEditTitle"
          @keydown.enter="finishEditTitle"
          @keydown.esc="cancelEditTitle"
          ref="titleInputRef"
          :class="{ 'line-through text-gray-400': todo.completed }"
          :readonly="todo.completed"
          class="flex-1 text-sm font-medium bg-transparent border-none outline-none px-0 py-0 cursor-text focus:ring-0"
        />
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex items-center gap-2 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
        <!-- 折叠按钮 -->
        <button
          @click="isCollapsed = !isCollapsed"
          class="flex-shrink-0 text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-50 transition-transform"
          :class="{ 'rotate-90': isCollapsed }"
          title="折叠/展开"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
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
          v-if="!todo.completed"
          @click="handleAddItem"
          class="text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-50 active:scale-95"
          title="添加待办"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <button
          @click="$emit('delete', todo.id)"
          class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
          title="删除组"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 组内待办列表 -->
    <div v-if="!isCollapsed" class="space-y-2 p-3 bg-gray-50">
      <div
        v-for="item in sortedGroupItems"
        :key="item.id"
        class="flex items-center gap-3 bg-white px-3 py-2 rounded-lg min-h-[40px] group/item"
      >
        <input 
          type="checkbox" 
          :checked="item.completed" 
          @change="$emit('toggle-item', item.id)" 
          class="flex-shrink-0 cursor-pointer"
        />
        <input
          v-model="editingItems[item.id]"
          @blur="finishEditItem(item.id)"
          @keydown.esc="cancelEditItem(item.id)"
          @keydown.enter.prevent="handleItemEnter(item.id)"
          :ref="el => setItemInputRef(item.id, el)"
          :class="{ 'line-through text-gray-400': item.completed }"
          :placeholder="item.completed ? '' : '（待输入）'"
          :readonly="item.completed"
          class="flex-1 text-sm bg-transparent border-none outline-none px-0 py-0 cursor-text focus:ring-0"
        />
        <button
          @click="$emit('delete-item', item.id)"
          class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95 transition-opacity flex-shrink-0 md:opacity-0 md:group-hover/item:opacity-100"
          title="删除待办"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from "vue";
import type { Todo } from "../stores/data";

const props = defineProps<{
  todo: Todo;
}>();

const emit = defineEmits<{
  toggle: [id: number];
  "update-title": [id: number, title: string];
  delete: [id: number];
  pin: [id: number];
  "add-item": [groupId: number];
  "update-item-title": [id: number, title: string];
  "toggle-item": [id: number];
  "delete-item": [id: number];
}>();

const isCollapsed = ref(false);
const editTitle = ref(props.todo.title);
const titleInputRef = ref<HTMLInputElement | null>(null);
const editingItems = ref<Record<number, string>>({});
const itemInputRefs = ref<Record<number, HTMLInputElement | null>>({});
const focusOnNextNewItem = ref(false);
// 记录之前的待办 ID 列表，用于检测新添加的待办
const previousItemIds = ref<Set<number>>(new Set());

// 排序后的组内待办（按创建时间正序，最新的在下面）
const sortedGroupItems = computed(() => {
  if (!props.todo.group_items) return [];
  return [...props.todo.group_items].sort((a, b) => {
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();
    return timeA - timeB; // 正序：旧的在上，新的在下
  });
});

// 监听组标题的变化
watch(() => props.todo.title, (newTitle) => {
  editTitle.value = newTitle;
});

const finishEditTitle = () => {
  if (props.todo.completed) return; // 已完成的不能编辑
  if (editTitle.value.trim() && editTitle.value !== props.todo.title) {
    emit("update-title", props.todo.id, editTitle.value.trim());
  } else {
    // 如果内容为空或未改变，恢复原值
    editTitle.value = props.todo.title;
  }
};

const cancelEditTitle = () => {
  editTitle.value = props.todo.title;
};

const handleAddItem = () => {
  focusOnNextNewItem.value = true;
  emit("add-item", props.todo.id);
};

// 设置输入框引用
const setItemInputRef = (itemId: number, el: any) => {
  if (el && el instanceof HTMLInputElement) {
    itemInputRefs.value[itemId] = el;
  } else if (el && '$el' in el && el.$el instanceof HTMLInputElement) {
    itemInputRefs.value[itemId] = el.$el;
  }
};

// 初始化组内待办的编辑状态
const initializeItemEditing = () => {
  if (props.todo.group_items) {
    props.todo.group_items.forEach(item => {
      editingItems.value[item.id] = item.title || "";
    });
  }
};

// 监听组内待办的变化
watch(() => props.todo.group_items, (newItems: typeof props.todo.group_items) => {
  if (newItems) {
    const currentItemIds = new Set(newItems.map(item => item.id));
    
    // 检测是否有新待办添加（通过比较 ID 集合）
    const hasNewItem = newItems.length > previousItemIds.value.size || 
      [...currentItemIds].some(id => !previousItemIds.value.has(id));
    
    newItems.forEach((item) => {
      if (!(item.id in editingItems.value)) {
        editingItems.value[item.id] = item.title || "";
      } else {
        // 如果已存在，同步更新值
        editingItems.value[item.id] = item.title || "";
      }
    });
    
    if (focusOnNextNewItem.value && !hasNewItem) {
      focusOnNextNewItem.value = false;
    }

    // 当有新待办添加时，尝试聚焦到最后一个（仅限用户主动新增）
    if (hasNewItem && focusOnNextNewItem.value && newItems.length > 0) {
      focusOnNextNewItem.value = false;
      nextTick(() => {
        // 按创建时间排序，找到最新的（最后一个）
        const sorted = [...newItems].sort((a, b) => {
          const timeA = new Date(a.created_at).getTime();
          const timeB = new Date(b.created_at).getTime();
          return timeA - timeB; // 正序
        });
        const lastItem = sorted[sorted.length - 1];

        // 使用重试机制确保 ref 已设置
        const tryFocus = (attempts = 0) => {
          setTimeout(() => {
            const input = itemInputRefs.value[lastItem.id];
            if (input) {
              input.focus();
              const length = input.value.length;
              input.setSelectionRange(length, length);
            } else if (attempts < 5) {
              tryFocus(attempts + 1);
            }
          }, attempts === 0 ? 100 : 50);
        };
        tryFocus();
      });
    }

    // 更新记录的 ID 集合
    previousItemIds.value = currentItemIds;
  }
}, { deep: true });

const finishEditItem = (itemId: number) => {
  const item = props.todo.group_items?.find(i => i.id === itemId);
  if (!item || item.completed) return; // 已完成的不能编辑
  
  const title = editingItems.value[itemId]?.trim() || "";
  if (title && title !== item.title) {
    emit("update-item-title", itemId, title);
  } else if (!title && item.title) {
    // 如果内容为空但原值不为空，恢复原值
    editingItems.value[itemId] = item.title;
  }
};

const cancelEditItem = (itemId: number) => {
  const item = props.todo.group_items?.find(i => i.id === itemId);
  if (item) {
    editingItems.value[itemId] = item.title || "";
  }
};

// 处理组内待办回车：保存当前待办并创建新待办
const handleItemEnter = async (itemId: number) => {
  const title = editingItems.value[itemId]?.trim() || "";
  
  // 如果当前待办有内容，先保存（异步等待保存完成）
  if (title) {
    emit("update-item-title", itemId, title);
    // 等待一个 tick 确保更新完成
    await nextTick();
  }
  
  // 创建新待办（由本组件决定是否需要聚焦新待办）
  focusOnNextNewItem.value = true;
  emit("add-item", props.todo.id);
};

// 监听全局事件：聚焦第一个待办
const handleFocusFirstItem = (event: CustomEvent) => {
  if (event.detail.groupId === props.todo.id && props.todo.group_items && props.todo.group_items.length > 0) {
    nextTick(() => {
      const firstItem = props.todo.group_items![0];
      const input = itemInputRefs.value[firstItem.id];
      input?.focus();
      // 将光标移到末尾
      if (input) {
        const length = input.value.length;
        input.setSelectionRange(length, length);
      }
    });
  }
};

// 监听全局事件：聚焦最后一个待办
const handleFocusLastItem = (event: CustomEvent) => {
  if (event.detail.groupId === props.todo.id) {
    // 使用多次 nextTick 和 setTimeout 确保 DOM 和数据都更新完成
    nextTick(() => {
      setTimeout(() => {
        nextTick(() => {
          if (props.todo.group_items && props.todo.group_items.length > 0) {
            const lastItem = props.todo.group_items[props.todo.group_items.length - 1];
            // 尝试多次查找输入框，因为 ref 可能还没设置好
            const tryFocus = (attempts = 0) => {
              const input = itemInputRefs.value[lastItem.id];
              if (input) {
                input.focus();
                // 全选文本
                input.select();
              } else if (attempts < 5) {
                // 如果还没找到，再等一会儿重试
                setTimeout(() => tryFocus(attempts + 1), 50);
              }
            };
            tryFocus();
          }
        });
      }, 100);
    });
  }
};

onMounted(() => {
  window.addEventListener('focus-first-item', handleFocusFirstItem as EventListener);
  window.addEventListener('focus-last-item', handleFocusLastItem as EventListener);
  // 初始化组标题的编辑状态
  editTitle.value = props.todo.title;
  // 初始化组内待办的编辑状态
  initializeItemEditing();
});

onUnmounted(() => {
  window.removeEventListener('focus-first-item', handleFocusFirstItem as EventListener);
  window.removeEventListener('focus-last-item', handleFocusLastItem as EventListener);
});
</script>

<style scoped>
/* 确保输入框没有黑边 */
input[type="text"] {
  @apply border-gray-200;
}
</style>

