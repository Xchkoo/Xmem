<template>
  <!-- 未登录时显示登录注册页面 -->
  <Auth v-if="!user.token" />
  
  <!-- 笔记库界面 -->
  <NotesView v-else-if="currentView === 'notes'" :highlight-note-id="selectedNoteId" @back="currentView = 'main'; selectedNoteId = null" />
  
  <!-- 已登录时显示主界面 -->
  <div v-else class="min-h-screen bg-primary text-gray-900 flex flex-col items-center">
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
                  📎 选择文件
                  <input type="file" @change="onFile" class="hidden" />
                </label>
                <button class="btn ghost" @click="pasteFromClipboard">📋 粘贴</button>
              </div>
              <div class="flex gap-3">
                <button class="btn ghost" @click="inputText = ''">清空</button>
                <button class="btn primary" @click="handleSubmit">提交到 {{ currentLabel }}</button>
              </div>
            </div>
          </div>

          <!-- 笔记模式：只显示最新笔记 -->
          <div v-if="currentTab === 'note'">
            <div class="flex items-center justify-between mb-2">
              <div class="section-title">最新笔记</div>
              <div class="flex items-center gap-3">
                <button
                  v-if="data.notes.length > noteDisplayLimit && noteDisplayLimit < 18"
                  @click="noteDisplayLimit = 18"
                  class="text-sm text-gray-600 hover:text-gray-900 underline"
                >
                  显示更多 ({{ noteDisplayLimit }}/{{ Math.min(data.notes.length, 18) }})
                </button>
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
                v-for="note in data.notes.slice(0, noteDisplayLimit)"
                :key="note.id"
                class="card relative group hover:shadow-lg transition-all duration-200 cursor-pointer"
                @click="handleNoteClick(note.id)"
              >
                <div 
                  class="text-gray-800 whitespace-pre-line pr-10 pb-10 break-words note-content"
                  :class="{ 'note-collapsed': isNoteCollapsed(note) }"
                >
                  {{ note.body }}
                </div>
                <div v-if="isNoteCollapsed(note)" class="text-xs text-blue-500 mt-2 mb-2">点击查看完整内容 →</div>
                <div class="text-xs text-gray-400 mt-2 absolute bottom-2 left-4">{{ formatTime(note.created_at) }}</div>
                <button
                  @click.stop="data.removeNote(note.id)"
                  class="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
                  title="删除笔记"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
            <p v-else class="text-gray-400 text-sm">暂无笔记</p>
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

    <FabMenu @settings="openSettings" @notes="currentView = 'notes'" @ledger="scrollToSection('ledger')" />
    
    <!-- 设置界面 -->
    <Settings :visible="showSettings" @close="showSettings = false" />
    
    <!-- Toast 提示 -->
    <transition name="toast">
      <div
        v-if="showToast"
        class="fixed top-4 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ toastMessage }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import TabSwitcher from "./components/TabSwitcher.vue";
import FabMenu from "./components/FabMenu.vue";
import Auth from "./components/Auth.vue";
import Settings from "./components/Settings.vue";
import NotesView from "./components/NotesView.vue";
import { useUserStore } from "./stores/user";
import { useDataStore } from "./stores/data";

const tabs = [
  { label: "笔记模式", value: "note" },
  { label: "记账模式", value: "ledger" }
];
const currentTab = ref<"note" | "ledger">("note");
const currentView = ref<"main" | "notes">("main");
const noteDisplayLimit = ref(9); // 默认显示9个，最多18个
const selectedNoteId = ref<number | null>(null); // 用于跳转到笔记库时定位
const inputText = ref("");
const todoText = ref("");
const showSettings = ref(false);
const toastMessage = ref("");
const showToast = ref(false);

const user = useUserStore();
const data = useDataStore();

const currentLabel = computed(() => (currentTab.value === "note" ? "笔记库" : "记账"));

onMounted(async () => {
  if (user.token) {
    await user.fetchProfile();
    await data.loadAll();
  }
});

const handleSubmit = async () => {
  if (!inputText.value.trim()) return;
  if (currentTab.value === "note") {
    await data.addNote(inputText.value);
  } else {
    await data.addLedger(inputText.value);
  }
  inputText.value = "";
};

// Toast 提示
const showToastMessage = (message: string) => {
  toastMessage.value = message;
  showToast.value = true;
  setTimeout(() => {
    showToast.value = false;
  }, 3000);
};

const addTodo = async () => {
  if (!todoText.value.trim()) {
    showToastMessage("待办内容不能为空");
    return;
  }
  
  if (todoText.value.length > 50) {
    showToastMessage("待办事项不能超过50字");
    return;
  }
  
  await data.addTodo(todoText.value);
  todoText.value = "";
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

const scrollToSection = (type: "notes" | "ledger") => {
  // 简单滚动示意，需结合实际标记
  window.scrollTo({ top: 200, behavior: "smooth" });
};

const openSettings = () => {
  showSettings.value = true;
};

// 判断笔记是否需要折叠（超过150字符或超过5行）
const isNoteCollapsed = (note: { body: string }) => {
  return note.body.length > 150 || note.body.split('\n').length > 5;
};

// 处理笔记点击
const handleNoteClick = (noteId: number) => {
  selectedNoteId.value = noteId;
  currentView.value = 'notes';
};

// 跳转到笔记库
const goToNotesView = () => {
  selectedNoteId.value = null;
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

/* 笔记折叠样式 */
.note-content.note-collapsed {
  max-height: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 5;
  line-clamp: 5;
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
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.3s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>

