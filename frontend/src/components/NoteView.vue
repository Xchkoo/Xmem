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
        <div class="text-xl font-bold">查看笔记</div>
      </div>
      <button
        @click="$emit('edit')"
        class="btn primary flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        编辑
      </button>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div v-if="note" class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <!-- 笔记内容 -->
        <div class="prose prose-lg max-w-none mb-6">
          <div 
            class="text-gray-800 break-words"
            v-html="renderedContent"
          />
        </div>

        <!-- 笔记信息 -->
        <div class="border-t pt-4 flex items-center justify-between">
          <div class="text-xs text-gray-400">
            创建时间：{{ formatTime(note.created_at) }}
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="copyNoteText"
              class="btn ghost text-sm"
              title="复制文本"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              复制
            </button>
            <button
              @click="handleDelete"
              class="btn ghost text-sm text-red-500 hover:text-red-700"
              title="删除笔记"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              删除
            </button>
          </div>
        </div>
      </div>
      <div v-else class="bg-white rounded-3xl shadow-float p-6 md:p-8 text-center">
        <p class="text-gray-400 text-lg">笔记不存在</p>
      </div>
    </main>
    
    <!-- FabMenu -->
    <FabMenu 
      @settings="() => {}" 
      @notes="() => {}" 
      @home="$emit('back')"
      @ledger="() => {}" 
    />
    
    <!-- 确认对话框 -->
    <ConfirmDialog
      :visible="confirm.visible"
      :title="confirm.title"
      :message="confirm.message"
      :confirm-text="confirm.confirmText"
      :cancel-text="confirm.cancelText"
      :type="confirm.type"
      @confirm="confirm.confirm()"
      @cancel="confirm.cancel()"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { marked } from "marked";
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { useConfirmStore } from "../stores/confirm";
import ConfirmDialog from "./ConfirmDialog.vue";

interface Props {
  noteId: number | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  back: [];
  edit: [];
  deleted: [];
}>();

const data = useDataStore();
const toast = useToastStore();
const confirm = useConfirmStore();

// 获取笔记
const note = computed(() => {
  if (!props.noteId) return null;
  return data.notes.find(n => n.id === props.noteId) || null;
});

// 渲染笔记内容
const renderedContent = computed(() => {
  if (!note.value || !note.value.body_md) return "";
  let html = marked(note.value.body_md) as string;
  // 确保所有链接在新窗口打开，文件链接添加下载属性
  html = html.replace(/<a href="([^"]+)">/g, (match: string, url: string) => {
    // 如果是文件链接（不是图片），添加下载属性
    if (!url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
      return `<a href="${url}" target="_blank" download>`;
    }
    return `<a href="${url}" target="_blank">`;
  });
  return html;
});

// 复制笔记文本
const copyNoteText = async () => {
  if (!note.value || !note.value.body_md) return;
  
  const content = note.value.body_md;
  
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
const handleDelete = async () => {
  if (!note.value) return;
  
  const result = await confirm.show({
    title: "删除笔记",
    message: "确定要删除这条笔记吗？删除后无法恢复。",
    confirmText: "删除",
    cancelText: "取消",
    type: "danger",
  });

  if (result) {
    try {
      await data.removeNote(note.value.id);
      toast.success("笔记删除成功");
      emit("deleted");
    } catch (error: any) {
      console.error("删除笔记失败:", error);
      toast.error(error.response?.data?.detail || "笔记删除失败，请重试");
    }
  }
};

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return "";
  let dateStr = timeStr;
  const hasTimezone = timeStr.includes("Z") || /[+-]\d{2}:\d{2}$/.test(timeStr);
  if (!hasTimezone && timeStr.includes("T")) {
    dateStr = timeStr + "Z";
  }
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) {
    return "刚刚";
  } else if (minutes < 60) {
    return `${minutes}分钟前`;
  } else if (hours < 24) {
    return `${hours}小时前`;
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    
    if (year === now.getFullYear()) {
      return `${month}-${day} ${hour}:${minute}`;
    } else {
      return `${year}-${month}-${day} ${hour}:${minute}`;
    }
  }
};

// 确保笔记已加载
onMounted(async () => {
  if (props.noteId && data.notes.length === 0) {
    await data.fetchNotes();
  }
});
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}

.prose {
  @apply text-gray-800;
}

.prose :deep(h1) {
  @apply text-3xl font-bold mt-6 mb-4;
}

.prose :deep(h2) {
  @apply text-2xl font-bold mt-5 mb-3;
}

.prose :deep(h3) {
  @apply text-xl font-bold mt-4 mb-2;
}

.prose :deep(p) {
  @apply mb-4;
}

.prose :deep(ul), .prose :deep(ol) {
  @apply list-disc list-inside mb-4;
}

.prose :deep(code) {
  @apply bg-gray-200 px-1 rounded text-sm;
}

.prose :deep(pre) {
  @apply bg-gray-100 p-4 rounded mb-4 overflow-x-auto;
}

.prose :deep(blockquote) {
  @apply border-l-4 border-gray-300 pl-4 italic my-4;
}

.prose :deep(a) {
  @apply text-blue-600 hover:underline;
}

.prose :deep(img) {
  @apply max-w-full rounded my-4;
}
</style>


