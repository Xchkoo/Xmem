<template>
  <!-- 未登录时显示登录注册页面 -->
  <Auth v-if="!user.token" />
  
  <!-- 笔记编辑器界面 -->
  <NoteEditor v-else-if="currentView === 'editor'" :note-id="editingNoteId" @cancel="handleEditorCancel" @saved="handleNoteSaved" />
  
  <!-- 查看笔记界面 -->
  <NoteView v-else-if="currentView === 'note-view'" :note-id="viewingNoteId" @back="handleNoteViewBack" @edit="handleNoteViewEdit" @deleted="handleNoteViewDeleted" />
  
  <!-- 笔记库界面 -->
  <NotesView v-else-if="currentView === 'notes'" @back="currentView = 'main'" @new-note="handleNewNote" @view-note="handleViewNote" />
  
  <!-- 已登录时显示主界面 -->
  <div v-else-if="user.token" class="min-h-screen bg-primary text-gray-900 flex flex-col items-center">
    <header class="w-full max-w-4xl px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="text-xl font-bold">Xmem 个人记账 + 待办</div>
      <div class="flex items-center gap-3 text-sm">
        <span class="text-gray-600">{{ getGreeting() }}，{{ user.profile?.user_name || user.profile?.email }}</span>
        <button class="btn ghost" @click="user.logout()">登出</button>
      </div>
    </header>

    <main class="w-full max-w-4xl px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <TabSwitcher v-model="currentTab" :tabs="tabs" />
        </div>

        <div class="space-y-6">
          <div class="bg-primary rounded-2xl p-4 md:p-6 shadow-inner">
            <label class="block text-gray-600 text-sm mb-2">快速输入</label>
            <textarea
              v-model="inputText"
              class="input h-32 md:h-40"
              placeholder="贴上文字或描述，自动按当前分页归类"
            />
            <div class="flex flex-wrap justify-between items-center gap-3 mt-3">
              <div class="flex gap-3">
                <label class="btn ghost cursor-pointer">
                  📷 插入图片
                  <input type="file" accept="image/*" multiple @change="handleImageUpload" class="hidden" />
                </label>
                <label class="btn ghost cursor-pointer">
                  📎 插入文件
                  <input type="file" multiple @change="handleFileUpload" class="hidden" />
                </label>
                <button class="btn ghost" @click="pasteFromClipboard">📋 粘贴</button>
              </div>
              <div class="flex gap-3">
                <button class="btn ghost" @click="clearInput">清空</button>
                <button class="btn primary" @click="handleSubmit">提交到 {{ currentLabel }}</button>
              </div>
            </div>
            <!-- 已上传的文件列表 -->
          </div>

          <!-- 笔记模式：只显示最新笔记 -->
          <div v-if="currentTab === 'note'">
            <div class="flex items-center justify-between mb-2">
              <div class="section-title">最新笔记</div>
              <div class="flex items-center gap-3">
                <button
                  @click="goToNotesView()"
                  class="text-sm text-gray-600 hover:text-gray-900 underline"
                >
                  查看全部 →
                </button>
              </div>
            </div>
            <div v-if="data.notes.length" class="notes-masonry">
              <div
                v-for="note in displayedNotes"
                :key="note.id"
                class="card relative group hover:shadow-lg transition-all duration-200 cursor-pointer"
                @click="handleNoteClick(note.id)"
              >
                <div 
                  :ref="(el) => handleNoteHeightRef(el, note.id)"
                  class="text-gray-800 pr-10 pb-10 break-words note-content prose prose-sm max-w-none"
                  :class="{ 'note-collapsed': isNoteCollapsed(note) }"
                  v-html="renderNoteContent(note)"
                />
                <div v-if="isNoteCollapsed(note)" class="text-xs text-blue-500 mt-2 mb-2">点击查看完整内容 →</div>
                <div class="text-xs text-gray-400 mt-2 absolute bottom-2 left-4">{{ formatTime(note.created_at) }}</div>
                <div class="absolute bottom-2 right-2 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    @click.stop="copyNoteText(note)"
                    class="text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-50 active:scale-95"
                    title="复制文本"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                  <button
                    @click.stop="handleDeleteNote(note.id)"
                    class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
                    title="删除笔记"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              <!-- 如果笔记超过显示限制，显示省略号卡片 -->
              <div
                v-if="remainingNotesCount > 0"
                @click="goToNotesView()"
                class="card relative group hover:shadow-lg transition-all duration-200 cursor-pointer flex items-center justify-center min-h-[200px] bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-dashed border-gray-300 hover:border-gray-400"
              >
                <div class="text-center">
                  <div class="text-4xl font-light text-gray-400 mb-2">⋯</div>
                  <div class="text-sm text-gray-600 font-medium">
                    还有 <span class="text-gray-900 font-semibold">{{ remainingNotesCount }}</span> 条笔记
                  </div>
                  <div class="text-xs text-gray-500 mt-1">点击查看全部</div>
                </div>
              </div>
            </div>
            <p v-else-if="!data.notes.length" class="text-gray-400 text-sm">暂无笔记</p>
          </div>

          <!-- 记账模式：只显示最新记账 -->
          <div v-if="currentTab === 'ledger'">
              <div class="section-title">最新记账</div>
              <div class="space-y-3">
                <div v-for="item in data.ledgers.slice(0, 4)" :key="item.id" class="card">
                  <div class="flex justify-between items-center">
                    <div class="font-semibold text-lg">
                      {{ item.amount ?? "待识别" }} <span class="text-sm text-gray-500">{{ item.currency }}</span>
                    </div>
                    <div class="text-sm text-gray-500">{{ item.category || "未分类" }}</div>
                  </div>
                  <p class="text-gray-700 mt-1">{{ item.raw_text }}</p>
                  <div class="text-xs text-gray-400 mt-2">{{ formatTime(item.created_at) }}</div>
                </div>
                <p v-if="!data.ledgers.length" class="text-gray-400 text-sm">暂无记账</p>
            </div>
          </div>

          <!-- 待办事项：只在笔记模式下显示 -->
          <div v-if="currentTab === 'note'">
            <div class="section-title">待办事项</div>
            <div class="bg-primary rounded-2xl p-4 shadow-inner flex flex-col gap-3">
              <div class="flex gap-2">
                <div class="flex-1 relative">
                  <input 
                    v-model="todoText" 
                    class="input flex-1 pr-12" 
                    placeholder="添加待办..." 
                    maxlength="50"
                  />
                  <span 
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none"
                    :class="{ 'text-red-500': todoText.length > 50 }"
                  >
                    {{ todoText.length }}/50
                  </span>
                </div>
                <button 
                  class="btn primary" 
                  @click="addTodo"
                  :disabled="todoText.length > 50"
                >
                  添加
                </button>
              </div>
              <div class="space-y-2">
                <label
                  v-for="todo in data.todos"
                  :key="todo.id"
                  class="flex items-center justify-between bg-white px-3 py-2 rounded-xl shadow"
                >
                  <div class="flex items-center gap-3">
                    <input type="checkbox" :checked="todo.completed" @change="data.toggleTodo(todo.id)" />
                    <span :class="{ 'line-through text-gray-400': todo.completed }">{{ todo.title }}</span>
                  </div>
                  <button 
                    class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95 transition-opacity"
                    @click="data.removeTodo(todo.id)"
                    title="删除待办"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- 全局组件：在所有已登录页面都显示 -->
  <!-- FabMenu 在所有页面都显示 -->
  <FabMenu 
    v-if="user.token"
    @settings="openSettings" 
    @notes="currentView = 'notes'" 
    @home="currentView = 'main'"
    @ledger="scrollToSection('ledger')" 
  />
  
  <!-- 设置界面 -->
  <Settings v-if="user.token" :visible="showSettings" @close="showSettings = false" />
  
  <!-- Toast 提示组件 -->
  <Toast v-if="user.token" />
  
  <!-- 确认对话框组件 -->
  <ConfirmDialog
    v-if="user.token"
    :visible="confirm.visible"
    :title="confirm.title"
    :message="confirm.message"
    :confirm-text="confirm.confirmText"
    :cancel-text="confirm.cancelText"
    :type="confirm.type"
    @confirm="confirm.confirm()"
    @cancel="confirm.cancel()"
  />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, nextTick } from "vue";
import TabSwitcher from "./components/TabSwitcher.vue";
import FabMenu from "./components/FabMenu.vue";
import Auth from "./components/Auth.vue";
import Settings from "./components/Settings.vue";
import NotesView from "./components/NotesView.vue";
import NoteEditor from "./components/NoteEditor.vue";
import NoteView from "./components/NoteView.vue";
import Toast from "./components/Toast.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import { useUserStore } from "./stores/user";
import { useDataStore } from "./stores/data";
import { useToastStore } from "./stores/toast";
import { useConfirmStore } from "./stores/confirm";
import { marked } from "marked";

const tabs = [
  { label: "笔记模式", value: "note" },
  { label: "记账模式", value: "ledger" }
];
const currentTab = ref<"note" | "ledger">("note");
const currentView = ref<"main" | "notes" | "editor" | "note-view">("main");
const editingNoteId = ref<number | null>(null); // 正在编辑的笔记ID
const viewingNoteId = ref<number | null>(null); // 正在查看的笔记ID
const inputText = ref("");
const todoText = ref("");
const showSettings = ref(false);

const user = useUserStore();
const data = useDataStore();
const toast = useToastStore();
const confirm = useConfirmStore();

const currentLabel = computed(() => (currentTab.value === "note" ? "笔记库" : "记账"));

// 响应式窗口宽度
const windowWidth = ref(typeof window !== "undefined" ? window.innerWidth : 1024);

// 根据屏幕尺寸计算应该显示的笔记数量
const maxNotesToShow = computed(() => {
  const width = windowWidth.value;
  if (width < 640) {
    // xs: 移动端小屏，显示 4 条
    return 4;
  } else if (width < 768) {
    // sm: 移动端大屏，显示 6 条
    return 6;
  } else if (width < 1024) {
    // md: 平板，显示 8 条
    return 8;
  } else if (width < 1280) {
    // lg: 桌面小屏，显示 10 条
    return 10;
  } else {
    // xl: 桌面大屏，显示 12 条
    return 12;
  }
});

// 显示的笔记列表
const displayedNotes = computed(() => {
  return data.notes.slice(0, maxNotesToShow.value);
});

// 剩余的笔记数量
const remainingNotesCount = computed(() => {
  return Math.max(0, data.notes.length - maxNotesToShow.value);
});

// 窗口大小变化监听
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

onMounted(async () => {
  if (user.token) {
    await user.fetchProfile();
    await data.loadAll();
  }
  // 监听窗口大小变化
  if (typeof window !== "undefined") {
    window.addEventListener("resize", handleResize);
    // 初始化窗口宽度
    windowWidth.value = window.innerWidth;
  }
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", handleResize);
  }
});

const handleSubmit = async () => {
  if (!inputText.value.trim()) return;
  
  if (currentTab.value === "note") {
    // 统一使用 body_md 格式
    await data.addNoteWithMD(inputText.value);
  } else {
    await data.addLedger(inputText.value);
  }
  clearInput();
};

const clearInput = () => {
  inputText.value = "";
};

const handleImageUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  for (const file of Array.from(files)) {
    try {
      const url = await data.uploadImage(file);
      // 直接在输入框中插入图片 markdown
      const markdown = `![图片](${url})\n`;
      inputText.value = inputText.value ? `${inputText.value}\n${markdown}` : markdown;
    } catch (err: any) {
      toast.error(err.message || "图片上传失败");
    }
  }
};

const handleFileUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  for (const file of Array.from(files)) {
    try {
      const fileInfo = await data.uploadFile(file);
      // 直接在输入框中插入文件 markdown
      const apiUrl = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
      const fullUrl = fileInfo.url.startsWith("http") ? fileInfo.url : `${apiUrl}${fileInfo.url}`;
      const markdown = `[${fileInfo.name}](${fullUrl})\n`;
      inputText.value = inputText.value ? `${inputText.value}\n${markdown}` : markdown;
    } catch (err: any) {
      toast.error(err.message || "文件上传失败");
    }
  }
};

const addTodo = async () => {
  if (!todoText.value.trim()) {
    toast.warning("待办内容不能为空");
    return;
  }
  
  if (todoText.value.length > 50) {
    toast.warning("待办事项不能超过50字");
    return;
  }
  
  await data.addTodo(todoText.value);
  todoText.value = "";
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

const scrollToSection = (type: "notes" | "ledger") => {
  // 简单滚动示意，需结合实际标记
  window.scrollTo({ top: 200, behavior: "smooth" });
};

const openSettings = () => {
  showSettings.value = true;
};

const handleNewNote = () => {
  editingNoteId.value = null;
  currentView.value = "editor";
};

const handleEditNote = (noteId: number) => {
  editingNoteId.value = noteId;
  currentView.value = "editor";
};

const handleEditorCancel = () => {
  editingNoteId.value = null;
  currentView.value = "notes";
};

const handleNoteSaved = () => {
  editingNoteId.value = null;
  currentView.value = "notes";
  data.fetchNotes(); // 刷新笔记列表
};

// 渲染笔记内容（支持markdown）
const renderNoteContent = (note: { body_md?: string | null }) => {
  const content = note.body_md || "";
  if (!content) return "";
  
  let html = marked(content) as string;
  // 确保所有链接在新窗口打开，文件链接添加下载属性
  html = html.replace(/<a href="([^"]+)">/g, (match: string, url: string) => {
    // 如果是文件链接（不是图片），添加下载属性
    if (!url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
      return `<a href="${url}" target="_blank" download>`;
    }
    return `<a href="${url}" target="_blank">`;
  });
  return html;
};

// 判断笔记是否需要折叠（基于实际渲染高度）
const noteHeights = ref<Map<number, boolean>>(new Map());

const checkNoteHeight = (noteId: number, element: HTMLElement | null) => {
  if (!element) return;
  nextTick(() => {
    const height = element.scrollHeight;
    const clientHeight = element.clientHeight;
    // 如果内容高度超过200px，需要折叠（调大了限制）
    noteHeights.value.set(noteId, height > 200);
  });
};

const isNoteCollapsed = (note: { id: number; body_md?: string | null }) => {
  return noteHeights.value.get(note.id) ?? false;
};

// 处理 ref 回调的辅助函数
const handleNoteHeightRef = (el: any, noteId: number) => {
  if (el && el.tagName) {
    checkNoteHeight(noteId, el as HTMLElement);
  }
};

// 处理笔记点击 - 跳转到查看笔记界面
const handleNoteClick = (noteId: number) => {
  viewingNoteId.value = noteId;
  currentView.value = 'note-view';
};

// 处理查看笔记界面的返回
const handleNoteViewBack = () => {
  viewingNoteId.value = null;
  currentView.value = 'main';
};

// 处理查看笔记界面的编辑
const handleNoteViewEdit = () => {
  editingNoteId.value = viewingNoteId.value;
  currentView.value = 'editor';
};

// 处理查看笔记界面的删除
const handleNoteViewDeleted = () => {
  viewingNoteId.value = null;
  currentView.value = 'main';
};

// 删除笔记（快速笔记区域）
const handleDeleteNote = async (noteId: number) => {
  try {
    await data.removeNote(noteId);
    toast.success("笔记删除成功");
  } catch (error: any) {
    console.error("删除笔记失败:", error);
    toast.error(error.response?.data?.detail || "笔记删除失败，请重试");
  }
};

// 处理笔记库的查看笔记
const handleViewNote = (noteId: number) => {
  viewingNoteId.value = noteId;
  currentView.value = 'note-view';
};

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

// 跳转到笔记库
const goToNotesView = () => {
  currentView.value = 'notes';
};

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 9) {
    return "早上好";
  } else if (hour >= 9 && hour < 12) {
    return "上午好";
  } else if (hour >= 12 && hour < 18) {
    return "下午好";
  } else {
    return "晚上好";
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
  @apply bg-gray-900 text-white shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
.card {
  @apply bg-white p-4 rounded-xl shadow;
}
.section-title {
  @apply text-sm font-semibold text-gray-500 mb-2;
}
.shadow-inner {
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.03), 0 6px 20px rgba(0, 0, 0, 0.05);
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
  max-width: 100%; /* 限制最大宽度 */
  margin-bottom: 0; /* Grid 布局不需要 margin-bottom，使用 gap */
  overflow: hidden; /* 防止内容溢出 */
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

/* Toast 动画 */
</style>

