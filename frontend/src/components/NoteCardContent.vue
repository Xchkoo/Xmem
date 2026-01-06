<template>
  <div>
    <!-- 笔记内容 -->
    <div 
      :ref="(el) => handleNoteHeightRef(el)"
      class="text-gray-800 pr-10 pb-10 break-words note-content relative"
      :class="{ 'note-collapsed': isCollapsed }"
      @dblclick="$emit('edit')"
    >
      <!-- 在列表视图中屏蔽所有交互（点击、图片放大等），只保留卡片本身的点击跳转 -->
      <div class="pointer-events-none" v-secure-display>
        <MdPreview 
          :editorId="`note-preview-${note.id}`" 
          :modelValue="displayContent" 
          class="md-preview-custom"
        />
      </div>
    </div>
    
    <!-- 折叠提示 -->
    <div v-if="isCollapsed" class="text-xs text-blue-500 mt-2 mb-2">点击查看完整内容 →</div>
    
    <!-- 时间和操作按钮 -->
    <div class="text-xs text-gray-400 mt-2 absolute bottom-2 left-4 flex items-center gap-2">
      <span v-if="note.is_pinned" class="text-yellow-500" title="已置顶">📌</span>
      <span>{{ formatTime(note.created_at) }}</span>
    </div>
    <div class="absolute bottom-2 right-2 flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
      <button
        @click.stop="$emit('pin')"
        class="text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-50 active:scale-95"
        :class="{ 'text-yellow-500': note.is_pinned }"
        :title="note.is_pinned ? '取消置顶' : '置顶'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      </button>
      <button
        @click.stop="$emit('copy')"
        class="text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-50 active:scale-95"
        title="复制文本"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </button>
      <button
        @click.stop="$emit('delete')"
        class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
        title="删除笔记"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onUnmounted } from "vue";
import type { Note } from "../stores/data";
import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';

const props = defineProps<{
  note: Note;
  searchQuery?: string;
}>();

const emit = defineEmits<{
  copy: [];
  delete: [];
  pin: [];
  edit: [];
}>();

// 处理搜索高亮
const displayContent = computed(() => {
  const content = props.note.body_md || '';
  if (!content || !props.searchQuery || !props.searchQuery.trim()) {
    return content;
  }
  
  const searchTerm = props.searchQuery.trim();
  const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escapedTerm})`, 'gi');
  
  return content.replace(regex, '<mark class="bg-yellow-200 text-gray-900">$1</mark>');
});

// 判断笔记是否需要折叠
const isCollapsed = ref(false);
let resizeObserver: ResizeObserver | null = null;

// 处理 ref 回调
const handleNoteHeightRef = (el: any) => {
  if (!el) {
    // 元素卸载时清理
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    return;
  }

  if (el instanceof HTMLElement) {
    // 如果已经有 observer，先断开
    if (resizeObserver) {
      resizeObserver.disconnect();
    }

    // 创建新的 observer 监听高度变化（包括图片加载撑开高度）
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        // 使用 scrollHeight 获取完整内容高度
        const height = entry.target.scrollHeight;
        isCollapsed.value = height > 200;
      }
    });

    resizeObserver.observe(el);
  }
};

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
});

const formatTime = (timeStr: string) => {
  if (!timeStr) return "";
  let dateStr = timeStr;
  const hasTimezone = timeStr.includes("Z") || /[+-]\d{2}:\d{2}$/.test(timeStr);
  
  if (!hasTimezone) {
    dateStr = timeStr + "Z";
  }
  
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
.note-collapsed {
  max-height: 200px;
  overflow: hidden;
}

/* 覆盖 MdPreview 的默认样式以适应卡片 */
:deep(.md-preview-custom) {
  background: transparent;
  padding: 0;
}
:deep(.md-editor-preview-wrapper) {
  padding: 0;
}
</style>
