<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-6xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
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
      <div class="flex items-center gap-3 text-sm">
        <span class="text-gray-600">你好，{{ user.profile?.user_name || user.profile?.email }}</span>
        <button class="btn ghost" @click="user.logout()">退出</button>
      </div>
    </header>

    <main class="w-full max-w-6xl mx-auto px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <!-- 快速输入区域 -->
        <div class="bg-primary rounded-2xl p-4 md:p-6 shadow-inner mb-6">
          <label class="block text-gray-600 text-sm mb-2">添加笔记</label>
          <textarea
            v-model="inputText"
            class="input h-32 md:h-40"
            placeholder="输入笔记内容..."
          />
          <div class="flex flex-wrap justify-between items-center gap-3 mt-3">
            <div class="flex gap-3">
              <label class="btn ghost cursor-pointer">
                📎 选择文件
                <input type="file" @change="onFile" class="hidden" />
              </label>
              <button class="btn ghost" @click="pasteFromClipboard">📋 粘贴</button>
            </div>
            <div class="flex gap-3">
              <button class="btn ghost" @click="inputText = ''">清空</button>
              <button class="btn primary" @click="handleAddNote" :disabled="!inputText.trim()">
                添加笔记
              </button>
            </div>
          </div>
        </div>

        <!-- 笔记列表 -->
        <div v-if="data.notes.length" class="notes-masonry">
          <div
            v-for="note in data.notes"
            :key="note.id"
            :id="`note-${note.id}`"
            :ref="el => { if (props.highlightNoteId === note.id && el) noteRef = el as HTMLElement }"
            class="card relative group hover:shadow-lg transition-all duration-200"
            :class="{ 'note-highlighted': shouldHighlight(note.id) }"
            @mouseenter="handleMouseEnter(note.id)"
            @mouseleave="handleMouseLeave()"
          >
            <div class="text-gray-800 whitespace-pre-line pr-10 pb-10 break-words">{{ note.body }}</div>
            <div class="text-xs text-gray-400 mt-2 absolute bottom-2 left-4">{{ formatTime(note.created_at) }}</div>
            <button
              @click="data.removeNote(note.id)"
              class="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
              title="删除笔记"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        <div v-else class="text-center py-12">
          <p class="text-gray-400 text-lg">还没有笔记</p>
          <p class="text-gray-400 text-sm mt-2">在上方输入框中添加你的第一条笔记吧</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue";
import { useUserStore } from "../stores/user";
import { useDataStore } from "../stores/data";

interface Props {
  highlightNoteId?: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  highlightNoteId: null
});

defineEmits<{
  back: [];
}>();

const user = useUserStore();
const data = useDataStore();
const inputText = ref("");
const noteRef = ref<HTMLElement | null>(null);
const isHighlighted = ref(false); // 控制是否显示高亮
const hoverTimer = ref<number | null>(null); // 鼠标悬停计时器

// 判断是否应该高亮显示
const shouldHighlight = (noteId: number) => {
  return props.highlightNoteId === noteId && isHighlighted.value;
};

// 处理鼠标进入
const handleMouseEnter = (noteId: number) => {
  if (props.highlightNoteId === noteId) {
    // 清除之前的计时器
    if (hoverTimer.value) {
      clearTimeout(hoverTimer.value);
    }
    // 2秒后取消高亮
    hoverTimer.value = window.setTimeout(() => {
      isHighlighted.value = false;
      hoverTimer.value = null;
    }, 2000);
  }
};

// 处理鼠标离开
const handleMouseLeave = () => {
  // 清除计时器
  if (hoverTimer.value) {
    clearTimeout(hoverTimer.value);
    hoverTimer.value = null;
  }
};

// 当 highlightNoteId 变化时，滚动到对应笔记并显示高亮
watch(() => props.highlightNoteId, async (newId) => {
  if (newId && noteRef.value) {
    await nextTick();
    noteRef.value.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // 显示高亮
    isHighlighted.value = true;
    // 清除之前的计时器
    if (hoverTimer.value) {
      clearTimeout(hoverTimer.value);
      hoverTimer.value = null;
    }
  } else {
    // 如果没有高亮ID，取消高亮
    isHighlighted.value = false;
  }
}, { immediate: true });

onMounted(async () => {
  // 如果初始就有 highlightNoteId，等待 DOM 渲染后滚动
  if (props.highlightNoteId) {
    await nextTick();
    if (noteRef.value) {
      noteRef.value.scrollIntoView({ behavior: 'smooth', block: 'center' });
      isHighlighted.value = true;
    }
  }
});

// 组件卸载前清理计时器
onBeforeUnmount(() => {
  if (hoverTimer.value) {
    clearTimeout(hoverTimer.value);
    hoverTimer.value = null;
  }
});

const handleAddNote = async () => {
  if (!inputText.value.trim()) return;
  await data.addNote(inputText.value);
  inputText.value = "";
};

const onFile = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  inputText.value = `${inputText.value}\n[附件] ${file.name}`.trim();
};

const pasteFromClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      inputText.value = inputText.value ? `${inputText.value}\n${text}` : text;
    }
  } catch (err) {
    console.error("读取剪切板失败:", err);
    alert("无法读取剪切板，请确保已授予剪切板访问权限");
  }
};

const formatTime = (timeStr: string) => {
  if (!timeStr) return "";
  // 如果时间字符串没有时区信息（没有 Z 或 +/- 时区偏移），假设它是 UTC 时间
  let dateStr = timeStr;
  // 检查是否包含时区信息：Z (UTC) 或 +/-HH:MM 格式
  const hasTimezone = timeStr.includes("Z") || /[+-]\d{2}:\d{2}$/.test(timeStr);
  if (!hasTimezone && timeStr.includes("T")) {
    dateStr = timeStr + "Z"; // 添加 UTC 标记
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
</script>

<style scoped>
.input {
  @apply w-full rounded-xl border border-gray-200 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm;
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
.card {
  @apply bg-white p-4 rounded-xl shadow;
}
.shadow-inner {
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.03), 0 6px 20px rgba(0, 0, 0, 0.05);
}

/* 网格布局 - 优先水平填充（从左到右填满一行） */
.notes-masonry {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  grid-auto-flow: row; /* 优先水平填充 */
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
  margin-bottom: 0; /* Grid 布局不需要 margin-bottom，使用 gap */
}

/* 笔记高亮样式 */
.note-highlighted {
  animation: highlightPulse 3s ease-in-out;
  border: 2px solid #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
}

@keyframes highlightPulse {
  0%, 100% {
    border-color: #3b82f6;
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
  }
  50% {
    border-color: #60a5fa;
    box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.1);
  }
}
</style>

