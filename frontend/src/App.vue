<template>
  <!-- eslint-disable vue/no-multiple-template-root -->
  <!-- 未登录时显示登录注册页面 -->
  <Auth v-if="!user.token" />
  
  <!-- 笔记编辑器界面 -->
  <NoteEditor v-else-if="currentView === 'editor'" :note-id="editingNoteId" @cancel="handleEditorCancel" @saved="handleNoteSaved" />
  
  <!-- 查看笔记界面 -->
  <NoteView v-else-if="currentView === 'note-view'" :note-id="viewingNoteId" @back="handleNoteViewBack" @edit="handleNoteViewEdit" @deleted="handleNoteViewDeleted" />
  
  <!-- 笔记库界面 -->
  <NotesView v-else-if="currentView === 'notes'" @back="currentView = 'main'" @new-note="handleNewNote" @view-note="handleViewNote" />
  
  <!-- 记账库界面 -->
  <LedgersView v-else-if="currentView === 'ledgers'" @back="currentView = 'main'" @view-ledger="handleViewLedger" @edit-ledger="handleEditLedger" @statistics="handleStatistics" />
  
  <!-- 记账统计界面 -->
  <LedgerStatisticsView v-else-if="currentView === 'ledger-statistics'" @back="currentView = 'ledgers'" />
  
  <!-- 查看记账界面 -->
  <LedgerView v-else-if="currentView === 'ledger-view'" :ledger-id="viewingLedgerId" @back="handleLedgerViewBack" @edit="handleLedgerViewEdit" />
  
  <!-- 已登录时显示主界面 -->
  <div v-else-if="user.token" class="min-h-screen bg-primary text-gray-900 flex flex-col items-center">
    <header class="w-full max-w-4xl px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="text-xl font-bold">Xmem</div>
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
            <!-- 按钮区域：手机视图下使用更紧凑的布局 -->
            <div class="mt-3 space-y-3">
              <!-- 第一行：操作按钮（手机视图下使用图标+短文字，桌面视图下使用完整文字） -->
              <div class="flex flex-wrap justify-between gap-2">
                <!-- 左侧按钮组 -->
                <div class="flex flex-wrap gap-2">
                  <label class="btn ghost cursor-pointer text-xs sm:text-sm px-2 sm:px-4 py-2 flex items-center gap-1.5">
                    <span>📷</span>
                    <span class="hidden sm:inline">{{ currentTab === 'ledger' ? '上传图片' : '插入图片' }}</span>
                    <span class="sm:hidden">{{ currentTab === 'ledger' ? '上传' : '图片' }}</span>
                    <input type="file" accept="image/*" :multiple="currentTab === 'note'" @change="handleImageUpload" class="hidden" />
                  </label>
                  <label v-if="currentTab === 'note'" class="btn ghost cursor-pointer text-xs sm:text-sm px-2 sm:px-4 py-2 flex items-center gap-1.5">
                    <span>📎</span>
                    <span class="hidden sm:inline">插入文件</span>
                    <span class="sm:hidden">文件</span>
                    <input type="file" multiple @change="handleFileUpload" class="hidden" />
                  </label>
                </div>
                <!-- 右侧按钮组 -->
                <div class="flex flex-wrap gap-2">
                  <button class="btn ghost text-xs sm:text-sm px-2 sm:px-4 py-2 flex items-center gap-1.5" @click="pasteFromClipboard">
                    <span>📋</span>
                    <span class="hidden sm:inline">粘贴</span>
                  </button>
                  <button class="btn ghost text-xs sm:text-sm px-2 sm:px-4 py-2" @click="clearInput" :disabled="isSubmitting">
                    清空
                  </button>
                </div>
              </div>
              
              <!-- 第二行：主要操作按钮 -->
              <div class="flex gap-2">
                <button 
                  v-if="currentTab === 'note'"
                  class="btn ghost text-xs sm:text-sm px-3 sm:px-4 py-2.5 flex items-center gap-1.5 whitespace-nowrap"
                  @click="handleNewNote"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                  <span class="hidden sm:inline">打开笔记编辑器</span>
                  <span class="sm:hidden">编辑器</span>
                </button>
                <button 
                  class="btn primary flex-1 text-sm sm:text-base py-2.5" 
                  @click="handleSubmit" 
                  :disabled="isSubmitting"
                >
                  {{ isSubmitting ? "提交中..." : `提交到 ${currentLabel}` }}
                </button>
              </div>
            </div>
            <!-- 记账模式下显示待提交的图片预览 -->
            <div v-if="currentTab === 'ledger' && pendingLedgerImage" class="mt-3 flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <img :src="pendingLedgerImagePreview" alt="待提交图片" class="w-20 h-20 object-cover rounded" />
              <div class="flex-1">
                <div class="text-sm text-gray-600">已选择图片，等待提交</div>
                <div class="text-xs text-gray-400 mt-1">可以在上方输入框中添加备注</div>
              </div>
              <button class="btn ghost text-sm" @click="clearPendingImage">移除</button>
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
                <NoteCardContent
                  :note="note"
                  :rendered-content="renderNoteContent(note)"
                  @copy="copyNoteText(note)"
                  @delete="handleDeleteNote(note.id)"
                  @pin="handlePinNote(note.id)"
                />
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
            <div class="flex items-center justify-between mb-2">
              <div class="section-title">最新记账</div>
              <div class="flex items-center gap-3">
                <button
                  @click="goToLedgersView()"
                  class="text-sm text-gray-600 hover:text-gray-900 underline"
                >
                  查看全部 →
                </button>
              </div>
            </div>
            <div v-if="data.ledgers.length" class="space-y-4">
              <template v-for="(group, date) in groupedLedgers" :key="date">
                <!-- 日期分割线 -->
                <div class="flex items-center gap-4 my-4">
                  <div class="flex-1 border-t border-gray-300"></div>
                  <div class="text-sm font-semibold text-gray-500 px-3">{{ date }}</div>
                  <div class="flex-1 border-t border-gray-300"></div>
                </div>
                <!-- 该日期的 ledger 列表 -->
                <div class="space-y-3">
                  <div
                    v-for="ledger in group"
                    :key="ledger.id"
                    class="card relative group hover:shadow-lg transition-all duration-200"
                    :class="{ 
                      'opacity-60': ledger.status === 'pending' || ledger.status === 'processing',
                      'border-2 border-blue-300 border-dashed': ledger.status === 'pending' || ledger.status === 'processing'
                    }"
                    @click="handleLedgerClick(ledger.id)"
                  >
                    <!-- Ledger 内容 -->
                    <LedgerCardContent :ledger="ledger" />
                    
                    <!-- 操作按钮（右下角） -->
                    <div class="absolute bottom-2 right-2 flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                      <button
                        v-if="ledger.status === 'completed'"
                        @click.stop="handleEditLedger(ledger)"
                        class="text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-50 active:scale-95"
                        title="编辑"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        @click.stop="handleDeleteLedger(ledger.id)"
                        class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
                        title="删除"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </template>
            </div>
            <p v-else-if="!data.ledgers.length" class="text-gray-400 text-sm">暂无记账</p>
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
              <div class="space-y-2 max-h-[300px] overflow-y-auto">
                <label
                  v-for="todo in data.todos"
                  :key="todo.id"
                  class="flex items-center justify-between bg-white px-3 py-2 rounded-xl shadow min-h-[44px]"
                >
                  <div class="flex items-center gap-3 flex-1 min-w-0">
                    <input type="checkbox" :checked="todo.completed" @change="data.toggleTodo(todo.id)" class="flex-shrink-0" />
                    <span 
                      :class="{ 'line-through text-gray-400': todo.completed }"
                      class="text-sm truncate flex-1"
                    >{{ todo.title }}</span>
                  </div>
                  <button 
                    class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95 transition-opacity flex-shrink-0 ml-2"
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

  <!-- 全局组件：在所有已登录页面都显示，除了编辑器界面 -->
  <!-- FabMenu 在所有页面显示，除了笔记编辑器 -->
  <FabMenu 
    v-if="user.token && currentView !== 'editor'"
    @settings="openSettings" 
    @notes="currentView = 'notes'" 
    @home="currentView = 'main'"
    @ledgers="goToLedgersView"
    @statistics="handleStatistics"
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
  
  <!-- Ledger 编辑弹窗 -->
  <LedgerEditor
    v-if="user.token"
    :visible="showLedgerEditor"
    :ledger="editingLedger"
    @close="showLedgerEditor = false; editingLedger = null"
    @saved="handleLedgerEditorSaved"
  />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, nextTick, watch } from "vue";
import TabSwitcher from "./components/TabSwitcher.vue";
import FabMenu from "./components/FabMenu.vue";
import Auth from "./components/Auth.vue";
import Settings from "./components/Settings.vue";
import NotesView from "./components/NotesView.vue";
import NoteEditor from "./components/NoteEditor.vue";
import NoteView from "./components/NoteView.vue";
import LedgersView from "./components/LedgersView.vue";
import LedgerView from "./components/LedgerView.vue";
import LedgerEditor from "./components/LedgerEditor.vue";
import LedgerCardContent from "./components/LedgerCardContent.vue";
import LedgerStatisticsView from "./components/LedgerStatisticsView.vue";
import NoteCardContent from "./components/NoteCardContent.vue";
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

// 从localStorage读取保存的tab，如果没有则默认"note"
const getSavedTab = (): "note" | "ledger" => {
  if (typeof window === "undefined") return "note";
  const saved = localStorage.getItem("currentTab");
  return (saved === "note" || saved === "ledger") ? saved : "note";
};

const currentTab = ref<"note" | "ledger">(getSavedTab());
const currentView = ref<"main" | "notes" | "editor" | "note-view" | "ledgers" | "ledger-view">("main");
const editingNoteId = ref<number | null>(null); // 正在编辑的笔记ID
const viewingNoteId = ref<number | null>(null); // 正在查看的笔记ID
const viewingLedgerId = ref<number | null>(null); // 正在查看的记账ID
const editingLedger = ref<LedgerEntry | null>(null); // 正在编辑的记账
const showLedgerEditor = ref(false); // 是否显示编辑弹窗
const previousView = ref<"main" | "notes" | "note-view">("main"); // 打开编辑器前的界面
const inputText = ref("");

// 从 localStorage 加载快速输入内容
const loadInputTextFromStorage = () => {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("quickInputText");
    if (saved) {
      inputText.value = saved;
    }
  }
};

// 保存快速输入内容到 localStorage
const saveInputTextToStorage = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem("quickInputText", inputText.value);
  }
};

// 监听 inputText 变化，自动保存到 localStorage
watch(inputText, () => {
  saveInputTextToStorage();
});
const todoText = ref("");
const showSettings = ref(false);
const isSubmitting = ref(false); // 提交状态，防止重复提交
// 记账模式下待提交的图片
const pendingLedgerImage = ref<File | null>(null);
const pendingLedgerImagePreview = ref<string>("");

// 轮询相关的状态
const pollingIntervals = ref<Map<number, number>>(new Map()); // ledgerId -> intervalId
const pollingTimeouts = ref<Map<number, number>>(new Map()); // ledgerId -> timeoutId
const POLLING_INTERVAL = 5000; // 5秒
const POLLING_TIMEOUT = 180000; // 3分钟

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
    return 3;
  } else if (width < 768) {
    // sm: 移动端大屏，显示 6 条
    return 5;
  } else if (width < 1024) {
    // md: 平板，显示 8 条
    return 8;
  } else if (width < 1280) {
    // lg: 桌面小屏，显示 10 条
    return 8;
  } else {
    // xl: 桌面大屏，显示 12 条
    return 11;
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

// 监听标签页切换，切换到笔记模式时清空待提交的图片，并保存到localStorage
watch(currentTab, (newTab) => {
  // 保存到localStorage
  if (typeof window !== "undefined") {
    localStorage.setItem("currentTab", newTab);
  }
  // 切换到笔记模式时清空待提交的图片
  if (newTab === "note") {
    clearPendingImage();
  }
});

onMounted(async () => {
  if (user.token) {
    await user.fetchProfile();
    await data.loadAll();
    
    // 检查是否有待处理的 ledger，如果有则开始轮询
    data.ledgers.forEach(ledger => {
      if (ledger.status === "pending" || ledger.status === "processing") {
        startPolling(ledger.id);
  }
});
    // 加载快速输入内容
    loadInputTextFromStorage();
  }
  // 监听窗口大小变化
  if (typeof window !== "undefined") {
    window.addEventListener("resize", handleResize);
    // 初始化窗口宽度
    windowWidth.value = window.innerWidth;
  }
});

onUnmounted(() => {
  // 清理所有轮询
  stopAllPolling();
  
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", handleResize);
  }
});

// 通用的提交 ledger 函数
const submitLedger = async (text?: string, imageFile?: File) => {
  try {
    const ledger = await data.addLedger(text, imageFile);
    // 如果状态是 pending 或 processing，开始轮询
    if (ledger.status === "pending" || ledger.status === "processing") {
      startPolling(ledger.id);
    }
    toast.success("已提交，正在识别中...");
    clearInput();
    clearPendingImage();
  } catch (error: any) {
    console.error("提交记账失败:", error);
    toast.error(error.response?.data?.detail || error.message || "记账失败");
    // 不重新抛出错误，避免导致调用者卡住
    // 清理状态，确保界面可以继续使用
    clearPendingImage();
    throw error; // 仍然抛出，但调用者应该捕获
  }
};

const handleSubmit = async () => {
  // 防止重复提交
  if (isSubmitting.value) {
    return;
  }
  
  if (currentTab.value === "note") {
    if (!inputText.value.trim()) return;
    isSubmitting.value = true;
    try {
    // 统一使用 body_md 格式
    await data.addNoteWithMD(inputText.value);
      clearInput();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || "笔记提交失败");
    } finally {
      isSubmitting.value = false;
    }
  } else {
    // 记账模式：需要文本或图片至少有一个
    if (!inputText.value.trim() && !pendingLedgerImage.value) {
      toast.warning("请输入文本或上传图片");
      return;
    }
    isSubmitting.value = true;
    try {
      const text = inputText.value.trim() || undefined;
      const imageFile = pendingLedgerImage.value || undefined;
      await submitLedger(text, imageFile);
    } catch (error: any) {
      // submitLedger 已经显示了错误提示，这里只需要确保不会卡住
      console.error("提交记账失败:", error);
    } finally {
      isSubmitting.value = false;
    }
  }
};

const clearInput = () => {
  inputText.value = "";
  // 同时清空 localStorage
  if (typeof window !== "undefined") {
    localStorage.removeItem("quickInputText");
  }
  if (currentTab.value === "ledger") {
    clearPendingImage();
  }
};

const clearPendingImage = () => {
  pendingLedgerImage.value = null;
  pendingLedgerImagePreview.value = "";
};

const handleImageUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  const file = Array.from(files)[0]; // 记账模式只支持单张图片
  
  if (currentTab.value === "ledger") {
    // 记账模式：先保存图片到前端，弹出确认对话框
    pendingLedgerImage.value = file;
    // 创建预览
    const reader = new FileReader();
    reader.onload = (e) => {
      pendingLedgerImagePreview.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
    
    // 弹出确认对话框
    const confirmed = await confirm.show({
      title: "上传图片",
      message: "是否直接提交到记账？",
      confirmText: "是，直接提交",
      cancelText: "否，我要添加备注",
      type: "info"
    });
    
    if (confirmed) {
      // 直接提交，使用输入框中的文本（如果有）
      try {
        const text = inputText.value.trim() || undefined;
        await submitLedger(text, file);
      } catch (error: any) {
        // submitLedger 已经显示了错误提示，这里只需要清理图片
        clearPendingImage();
      }
    }
    // 如果选择"否"，图片已保存到 pendingLedgerImage，等待用户输入备注后点击提交
  } else {
    // 笔记模式：直接上传并插入 markdown
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
  }
  
  // 清空文件输入，以便再次选择同一文件时也能触发 change 事件
  (e.target as HTMLInputElement).value = "";
};

const handleFileUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  for (const file of Array.from(files)) {
    try {
      const apiUrl = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
      const fileInfo = await data.uploadFile(file);
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
    toast.error("无法读取剪切板，请确保已授予剪切板访问权限");
  }
};

// 开始轮询 ledger 状态
const startPolling = (ledgerId: number) => {
  // 清除已存在的轮询（如果存在）
  stopPolling(ledgerId);
  
  let pollCount = 0;
  const maxPolls = POLLING_TIMEOUT / POLLING_INTERVAL; // 3分钟 / 5秒 = 36次
  let completed = false;
  
  const poll = async () => {
    // 如果已完成，不再轮询
    if (completed) return;
    
    try {
      const ledger = await data.fetchLedgerStatus(ledgerId);
      
      // 调试日志（开发环境）
      if (import.meta.env.DEV) {
        console.log(`[轮询] ledger ${ledgerId}: status = "${ledger.status}", amount = ${ledger.amount}`);
      }
      
      // 如果已完成或失败，停止轮询
      const status = String(ledger.status).toLowerCase().trim();
      if (status === "completed" || status === "failed") {
        completed = true;
        stopPolling(ledgerId);
        if (status === "completed") {
          toast.success("识别完成");
        } else {
          toast.error("识别失败，请重试");
        }
        return;
      }
      
      // 如果状态仍然是 pending 或 processing，继续轮询
      if (status === "pending" || status === "processing") {
        pollCount++;
        // 如果超过3分钟，停止轮询并提示
        if (pollCount >= maxPolls) {
          completed = true;
          stopPolling(ledgerId);
          toast.warning("识别超时，请稍后刷新查看结果");
          return;
        }
      } else {
        // 状态意外变化（可能是其他状态），停止轮询
        if (import.meta.env.DEV) {
          console.warn(`[轮询] Ledger ${ledgerId} 状态意外: "${ledger.status}"`);
        }
        completed = true;
        stopPolling(ledgerId);
      }
    } catch (error: any) {
      console.error("轮询失败:", error);
      // 轮询失败时不要立即停止，可能只是网络问题
      // 只在连续失败多次后才停止
      pollCount++;
      if (pollCount >= maxPolls) {
        completed = true;
        stopPolling(ledgerId);
      }
    }
  };
  
  // 立即执行第一次轮询
  poll();
  
  // 设置定时轮询
  const intervalId = window.setInterval(poll, POLLING_INTERVAL);
  pollingIntervals.value.set(ledgerId, intervalId);
  
  // 设置超时
  const timeoutId = window.setTimeout(() => {
    if (pollingIntervals.value.has(ledgerId)) {
      completed = true;
      stopPolling(ledgerId);
      toast.warning("识别超时，请稍后刷新查看结果");
    }
  }, POLLING_TIMEOUT);
  pollingTimeouts.value.set(ledgerId, timeoutId);
};

// 停止轮询
const stopPolling = (ledgerId: number) => {
  const intervalId = pollingIntervals.value.get(ledgerId);
  if (intervalId) {
    clearInterval(intervalId);
    pollingIntervals.value.delete(ledgerId);
  }
  
  const timeoutId = pollingTimeouts.value.get(ledgerId);
  if (timeoutId) {
    clearTimeout(timeoutId);
    pollingTimeouts.value.delete(ledgerId);
  }
};

// 停止所有轮询
const stopAllPolling = () => {
  pollingIntervals.value.forEach((intervalId) => {
    clearInterval(intervalId);
  });
  pollingIntervals.value.clear();
  
  pollingTimeouts.value.forEach((timeoutId) => {
    clearTimeout(timeoutId);
  });
  pollingTimeouts.value.clear();
};

const scrollToSection = (type: "notes" | "ledger") => {
  // 简单滚动示意，需结合实际标记
  window.scrollTo({ top: 200, behavior: "smooth" });
};

const openSettings = () => {
  showSettings.value = true;
};

const handleNewNote = () => {
  // 保存当前界面，以便返回时能回到正确的界面
  // 如果当前在主界面，保存为 main；如果在笔记库，保存为 notes
  if (currentView.value === "main" || currentView.value === "notes") {
    previousView.value = currentView.value;
  } else {
    // 如果从其他界面调用（不应该发生，但为了安全），默认返回主界面
    previousView.value = "main";
  }
  editingNoteId.value = null;
  currentView.value = "editor";
};

const handleEditNote = (noteId: number) => {
  // 保存当前界面，以便返回时能回到正确的界面
  // 如果当前在主界面，保存为 main；如果在笔记库，保存为 notes
  if (currentView.value === "main" || currentView.value === "notes") {
    previousView.value = currentView.value;
  } else {
    // 如果从其他界面调用（不应该发生，但为了安全），默认返回主界面
    previousView.value = "main";
  }
  editingNoteId.value = noteId;
  currentView.value = "editor";
};

const handleEditorCancel = () => {
  editingNoteId.value = null;
  // 返回到打开编辑器前的界面
  currentView.value = previousView.value;
};

const handleNoteSaved = () => {
  editingNoteId.value = null;
  // 返回到打开编辑器前的界面
  currentView.value = previousView.value;
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

// 注意：笔记折叠逻辑已移至 NoteCardContent 组件

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
  // 从 note-view 界面打开编辑器，返回时应该回到 note-view
  previousView.value = "note-view";
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
  // 检查快速删除设置
  const quickDeleteEnabled = typeof window !== "undefined" 
    ? localStorage.getItem("quickDeleteEnabled") === "true"
    : false;
  
  // 如果快速删除未启用，显示确认对话框
  if (!quickDeleteEnabled) {
    const result = await confirm.show({
      title: "确认删除",
      message: "确定要删除这条笔记吗？此操作不可恢复。",
      confirmText: "删除",
      cancelText: "取消",
      type: "danger",
    });
    
    if (!result) {
      return; // 用户取消删除
    }
  }
  
  // 执行删除
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

// Ledger 相关函数
const goToLedgersView = () => {
  currentView.value = "ledgers";
};

// 跳转到统计页
const handleStatistics = () => {
  currentView.value = "ledger-statistics";
};

// 按日期分组 ledger（只显示前12个）
const groupedLedgers = computed(() => {
  const groups: Record<string, LedgerEntry[]> = {};
  let count = 0;
  const maxCount = 12;
  
  for (const ledger of data.ledgers) {
    if (count >= maxCount) break;
    
    const date = new Date(ledger.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(ledger);
    count++;
  }
  return groups;
});

const handleLedgerClick = (ledgerId: number) => {
  viewingLedgerId.value = ledgerId;
  currentView.value = 'ledger-view';
};

const handleViewLedger = (ledgerId: number) => {
  viewingLedgerId.value = ledgerId;
  currentView.value = 'ledger-view';
};

const handleLedgerViewBack = () => {
  viewingLedgerId.value = null;
  currentView.value = 'ledgers';
};

const handleLedgerViewEdit = () => {
  const ledger = data.ledgers.find(l => l.id === viewingLedgerId.value);
  if (ledger) {
    editingLedger.value = ledger;
    showLedgerEditor.value = true;
  }
};

const handleEditLedger = (ledger: LedgerEntry) => {
  editingLedger.value = ledger;
  showLedgerEditor.value = true;
};

const handleDeleteLedger = async (ledgerId: number) => {
  const result = await confirm.show({
    title: "确认删除",
    message: "确定要删除这条记账吗？此操作不可恢复。",
    confirmText: "删除",
    cancelText: "取消",
    type: "danger",
  });

  if (result) {
    try {
      await data.removeLedger(ledgerId);
      toast.success("删除成功");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  }
};

const handleLedgerEditorSaved = () => {
  showLedgerEditor.value = false;
  editingLedger.value = null;
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

