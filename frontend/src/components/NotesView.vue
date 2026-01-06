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
        <div class="text-xl font-bold">笔记库</div>
      </div>
      <button
        @click="$emit('new-note')"
        class="btn primary flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加新笔记
      </button>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <!-- 搜索框 -->
        <div class="mb-6">
          <div class="relative">
            <input
              v-model="searchQuery"
              @input="handleSearch"
              type="text"
              placeholder="搜索笔记..."
              class="w-full rounded-xl border border-gray-200 bg-white !pl-11 pr-10 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm"
            />
            <!-- 搜索图标（始终显示） -->
            <div class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none flex items-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <!-- 清除按钮（有文本时显示） -->
            <button
              v-if="searchQuery"
              @click="clearSearch"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 搜索状态提示 -->
        <div v-if="isSearching" class="mb-4 text-center text-gray-500 text-sm">
          搜索中...
        </div>


        <!-- 笔记列表 -->
        <div v-if="!isSearching && data.notes.length" class="notes-masonry">
          <div
            v-for="note in data.notes"
            :key="note.id"
            class="card relative group hover:shadow-lg transition-all duration-200 cursor-pointer"
            @click="$emit('view-note', note.id)"
          >
            <NoteCardContent
              :note="note"
              :search-query="searchQuery"
              @copy="copyNoteText(note)"
              @delete="handleDeleteNote(note.id)"
              @pin="handlePinNote(note.id)"
              @edit="$emit('edit-note', note.id)"
            />
          </div>
        </div>
        <div v-else-if="!isSearching" class="text-center py-12">
          <p class="text-gray-400 text-lg">{{ searchQuery ? '没有找到匹配的笔记' : '还没有笔记' }}</p>
          <p v-if="!searchQuery" class="text-gray-400 text-sm mt-2">在上方输入框中添加你的第一条笔记吧</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";
import NoteCardContent from "./NoteCardContent.vue";

const emit = defineEmits<{
  back: [];
  "new-note": [];
  "view-note": [noteId: number];
  "edit-note": [noteId: number];
  settings: [];
  notes: [];
  ledger: [];
}>();

const data = useDataStore();
const toast = useToastStore();
const searchQuery = ref("");
const isSearching = ref(false);

// 搜索处理（防抖）
let searchTimeout: number | null = null;
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  searchTimeout = window.setTimeout(async () => {
    isSearching.value = true;
    try {
      const query = searchQuery.value.trim();
      // 明确传递搜索参数：如果有内容就传递，否则传递 undefined
      if (query) {
        await data.fetchNotes(query);
      } else {
        // 如果搜索框为空，加载所有笔记
        await data.fetchNotes();
      }
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      isSearching.value = false;
    }
  }, 300); // 300ms 防抖
};

// 清除搜索
const clearSearch = async () => {
  searchQuery.value = "";
  isSearching.value = true;
  try {
    await data.fetchNotes();
  } finally {
    isSearching.value = false;
  }
};

// 组件挂载时加载笔记
onMounted(async () => {
  // 如果 store 中没有笔记，或者有搜索关键词但 store 中可能不是搜索结果，则加载
  if (data.notes.length === 0 || searchQuery.value) {
    await data.fetchNotes();
  }
});

// 注意：笔记折叠逻辑已移至 NoteCardContent 组件

// 复制笔记文本（纯文本，不包括markdown格式和图片文件）
const copyNoteText = async (note: { body_md?: string | null }) => {
  const content = note.body_md || "";
  if (!content) return;
  
  // 移除markdown图片和文件链接，只保留纯文本
  let text = content
    .replace(/!\[.*?\]\(.*?\)/g, '') // 移除图片markdown
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // 将链接转换为文本
    .replace(/```[\s\S]*?```/g, '') // 移除代码块
    .replace(/`([^`]+)`/g, '$1') // 移除行内代码
    .replace(/#+\s+/g, '') // 移除标题标记
    .replace(/\*\*([^*]+)\*\*/g, '$1') // 移除粗体
    .replace(/\*([^*]+)\*/g, '$1') // 移除斜体
    .replace(/^\s*[-*+]\s+/gm, '') // 移除列表标记
    .replace(/^\s*>\s+/gm, '') // 移除引用标记
    .trim();
  
  try {
    await navigator.clipboard.writeText(text);
    toast.success("已复制到剪贴板");
  } catch (err) {
    console.error("复制失败:", err);
    toast.error("复制失败，请手动复制");
  }
};

// 删除笔记
const handleDeleteNote = async (noteId: number) => {
  try {
    await data.removeNote(noteId);
    toast.success("笔记删除成功");
  } catch (error: any) {
    console.error("删除笔记失败:", error);
    toast.error(error.response?.data?.detail || "笔记删除失败，请重试");
  }
};

// 置顶/取消置顶笔记
const handlePinNote = async (noteId: number) => {
  try {
    await data.togglePinNote(noteId);
    toast.success("操作成功");
  } catch (error: any) {
    console.error("置顶操作失败:", error);
    toast.error(error.response?.data?.detail || "操作失败，请重试");
  }
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
.card {
  @apply bg-white p-4 rounded-xl shadow;
}

/* 网格布局 */
.notes-masonry {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  grid-auto-flow: row;
}

@media (min-width: 768px) {
  .notes-masonry {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .notes-masonry {
    grid-template-columns: repeat(3, 1fr);
  }
}

.notes-masonry .card {
  width: 100%;
  max-width: 100%;
  margin-bottom: 0;
  overflow: hidden;
}

/* 笔记折叠样式 - 调大了高度限制 */
.note-content.note-collapsed {
  max-height: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 8;
  line-clamp: 8;
  -webkit-box-orient: vertical;
  position: relative;
}

.note-content.note-collapsed::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.95));
  pointer-events: none;
}

/* Markdown 渲染样式 */
.prose {
  @apply text-gray-800;
}

.prose :deep(h1) {
  @apply text-2xl font-bold mt-4 mb-2;
}

.prose :deep(h2) {
  @apply text-xl font-bold mt-3 mb-2;
}

.prose :deep(h3) {
  @apply text-lg font-bold mt-2 mb-1;
}

.prose :deep(p) {
  @apply mb-2;
}

.prose :deep(ul), .prose :deep(ol) {
  @apply list-disc list-inside mb-2;
}

.prose :deep(code) {
  @apply bg-gray-200 px-1 rounded text-sm;
}

.prose :deep(pre) {
  @apply bg-gray-100 p-2 rounded mb-2 overflow-x-auto;
}

.prose :deep(blockquote) {
  @apply border-l-4 border-gray-300 pl-4 italic my-2;
}

.prose :deep(a) {
  @apply text-blue-600 hover:underline;
}

.prose :deep(img) {
  @apply max-w-full rounded my-2;
}

/* 搜索高亮样式 */
.prose :deep(mark) {
  @apply bg-yellow-200 text-gray-900 px-1 rounded;
}
</style>
